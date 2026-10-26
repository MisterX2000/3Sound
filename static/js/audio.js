/**
 * Audio Engine for Soundboard
 * Handles polyphonic playback (Rapid Trigger), volume/mute control, loop toggle, and CSS-driven progress lifecycle.
 */
class AudioManager {
  constructor(options = {}) {
    this.masterVolume = options.volume ?? 0.8;
    this.isMuted = Boolean(options.muted);
    this.allowOverlap = options.allowOverlap ?? true;
    this.maxVoicesPerSound = options.maxVoicesPerSound ?? 10;
    this.onUpdate = options.onUpdate || (() => {});
    this.onPlay = options.onPlay || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.onStop = options.onStop || (() => {});
    this.onStopAll = options.onStopAll || (() => {});
    this.onLoopToggle = options.onLoopToggle || (() => {});
    this.onLoopCycle = options.onLoopCycle || (() => {});

    // soundId -> Set of active voice items: { id, audio, sound, isLooping, isStopped, endTimeoutId }
    this.activeAudios = new Map();
    // soundId -> string (id of newest voice triggered)
    this.latestVoiceIds = new Map();
  }

  setVolume(volume) {
    this.masterVolume = Math.min(1, Math.max(0, parseFloat(volume) || 0));
    this.syncVolumes();
  }

  setMuted(muted) {
    this.isMuted = Boolean(muted);
    this.syncVolumes();
  }

  setAllowOverlap(allow) {
    this.allowOverlap = Boolean(allow);
  }

  syncVolumes() {
    const effective = this.isMuted ? 0 : this.masterVolume;
    this.activeAudios.forEach((voices) => {
      voices.forEach((voice) => {
        voice.audio.volume = effective;
      });
    });
  }

  isPlaying(soundId) {
    const voices = this.activeAudios.get(soundId);
    return Boolean(voices && voices.size > 0);
  }

  isLooping(soundId) {
    const voices = this.activeAudios.get(soundId);
    if (!voices || voices.size === 0) return false;
    for (const v of voices) {
      if (v.isLooping && !v.isStopped) return true;
    }
    return false;
  }

  play(sound, startWithLoop = false) {
    const soundId = sound.id;

    // Solo mode: stop all active sounds first
    if (!this.allowOverlap) {
      this.stopAll();
    } else if (startWithLoop || this.isLooping(soundId)) {
      // Loop mode or currently looping: stop prior voices to avoid out-of-phase duplicate loops
      this.stop(soundId);
    }

    let voices = this.activeAudios.get(soundId);
    if (!voices) {
      voices = new Set();
      this.activeAudios.set(soundId, voices);
    }

    // Rapid Trigger polyphony limit: recycle oldest voice when reaching max voice limit
    if (voices.size >= this.maxVoicesPerSound) {
      const oldestVoice = voices.values().next().value;
      if (oldestVoice) {
        this.stopVoice(soundId, oldestVoice);
      }
    }

    const audio = new Audio(sound.sound_url);
    audio.preload = 'auto';
    audio.loop = Boolean(startWithLoop);
    audio.volume = this.isMuted ? 0 : this.masterVolume;

    const voice = {
      id: Math.random().toString(36).slice(2) + Date.now().toString(36),
      audio,
      sound,
      isLooping: Boolean(startWithLoop),
      isStopped: false,
      endTimeoutId: null
    };

    voices.add(voice);
    this.latestVoiceIds.set(soundId, voice.id);
    this.onUpdate(soundId, { isPlaying: true, isLooping: Boolean(startWithLoop) });

    // Trigger GPU animation when audio starts outputting sound
    audio.addEventListener('playing', () => {
      if (voice.isStopped) return;
      const duration = audio.duration && !isNaN(audio.duration) && audio.duration > 0
        ? audio.duration
        : (sound.duration && sound.duration > 0 ? sound.duration : 1);
      this.onPlay(soundId, { duration, isLooping: voice.isLooping });
    });

    // Re-synchronize loop iteration on audio seeked
    audio.addEventListener('seeked', () => {
      if (voice.isStopped || !voice.isLooping) return;
      this.onLoopCycle(soundId);
    });

    // Ended event: hold bar at 100% for 150ms, then fade out (250ms) before voice cleanup
    audio.addEventListener('ended', () => {
      if (voice.isStopped) return;

      const isLatest = this.latestVoiceIds.get(soundId) === voice.id;
      if (isLatest) {
        this.onEnd(soundId);
      }

      voice.endTimeoutId = setTimeout(() => {
        voice.endTimeoutId = null;
        this.cleanupVoice(soundId, voice);
      }, 450);
    });

    audio.addEventListener('error', (err) => {
      console.error('Audio playback error:', err);
      this.cleanupVoice(soundId, voice);
    });

    audio.play().catch((err) => {
      if (!voice.isStopped) {
        console.warn('Audio playback prevented or failed:', err);
      }
      this.cleanupVoice(soundId, voice);
    });
  }

  stopVoice(soundId, voice) {
    voice.isStopped = true;
    if (voice.endTimeoutId) {
      clearTimeout(voice.endTimeoutId);
      voice.endTimeoutId = null;
    }
    try {
      voice.audio.pause();
      voice.audio.removeAttribute('src');
      voice.audio.load();
    } catch (e) {}
    const voices = this.activeAudios.get(soundId);
    if (voices) {
      voices.delete(voice);
      if (voices.size === 0) {
        this.activeAudios.delete(soundId);
        this.latestVoiceIds.delete(soundId);
      }
    }
  }

  cleanupVoice(soundId, voice) {
    this.stopVoice(soundId, voice);
    const voices = this.activeAudios.get(soundId);
    if (!voices || voices.size === 0) {
      this.onUpdate(soundId, { isPlaying: false, isLooping: false });
    }
  }

  stop(soundId) {
    const voices = this.activeAudios.get(soundId);
    if (voices && voices.size > 0) {
      const voiceList = Array.from(voices);
      voiceList.forEach((voice) => {
        voice.isStopped = true;
        if (voice.endTimeoutId) {
          clearTimeout(voice.endTimeoutId);
          voice.endTimeoutId = null;
        }
        try {
          voice.audio.pause();
          voice.audio.removeAttribute('src');
          voice.audio.load();
        } catch (e) {}
      });
      this.activeAudios.delete(soundId);
      this.latestVoiceIds.delete(soundId);
      this.onStop(soundId);
      this.onUpdate(soundId, { isPlaying: false, isLooping: false });
    }
  }

  toggleLoop(sound) {
    const soundId = sound.id;
    if (this.isLooping(soundId)) {
      this.stop(soundId);
      return { isPlaying: false, isLooping: false };
    }

    this.play(sound, true);
    return { isPlaying: true, isLooping: true };
  }

  stopAll() {
    const entries = Array.from(this.activeAudios.entries());
    entries.forEach(([soundId, voices]) => {
      voices.forEach((voice) => {
        voice.isStopped = true;
        if (voice.endTimeoutId) {
          clearTimeout(voice.endTimeoutId);
          voice.endTimeoutId = null;
        }
        try {
          voice.audio.pause();
          voice.audio.removeAttribute('src');
          voice.audio.load();
        } catch (e) {}
      });
    });
    const ids = Array.from(this.activeAudios.keys());
    this.activeAudios.clear();
    this.latestVoiceIds.clear();
    this.onStopAll();
    ids.forEach((id) => {
      this.onUpdate(id, { isPlaying: false, isLooping: false });
    });
  }
}

if (typeof window !== 'undefined') {
  window.AudioManager = AudioManager;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AudioManager };
}
