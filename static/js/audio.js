/**
 * Audio Engine for Soundboard
 * Handles playback, volume/mute control, loop toggle, and CSS-driven progress lifecycle.
 */
class AudioManager {
  constructor(options = {}) {
    this.masterVolume = options.volume ?? 0.8;
    this.isMuted = Boolean(options.muted);
    this.allowOverlap = options.allowOverlap ?? true;
    this.onUpdate = options.onUpdate || (() => {});
    this.onPlay = options.onPlay || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.onStop = options.onStop || (() => {});
    this.onStopAll = options.onStopAll || (() => {});
    this.onLoopToggle = options.onLoopToggle || (() => {});
    this.onLoopCycle = options.onLoopCycle || (() => {});

    // soundId -> { audio, endTimeoutId, sound, isLooping, isStopped }
    this.activeAudios = new Map();
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
    this.activeAudios.forEach((item) => {
      item.audio.volume = effective;
    });
  }

  play(sound, startWithLoop = false) {
    const soundId = sound.id;

    // Solo mode: stop all active sounds first
    if (!this.allowOverlap) {
      this.stopAll();
    } else if (this.activeAudios.has(soundId)) {
      this.stop(soundId);
    }

    const audio = new Audio(sound.sound_url);
    audio.preload = 'auto';
    audio.loop = Boolean(startWithLoop);
    audio.volume = this.isMuted ? 0 : this.masterVolume;

    const activeItem = {
      audio,
      endTimeoutId: null,
      sound,
      isLooping: Boolean(startWithLoop),
      isStopped: false
    };

    // Store immediately so stop() or stopAll() can immediately reach and cancel this audio
    this.activeAudios.set(soundId, activeItem);
    this.onUpdate(soundId, { isPlaying: true, isLooping: activeItem.isLooping });

    // Trigger GPU animation when audio actually starts playing through speaker output
    audio.addEventListener('playing', () => {
      if (activeItem.isStopped) return;
      const duration = audio.duration && !isNaN(audio.duration) && audio.duration > 0
        ? audio.duration
        : (sound.duration && sound.duration > 0 ? sound.duration : 1);
      this.onPlay(soundId, { duration, isLooping: activeItem.isLooping });
    });

    // Re-synchronize loop iteration on audio seeked
    audio.addEventListener('seeked', () => {
      if (activeItem.isStopped || !activeItem.isLooping) return;
      this.onLoopCycle(soundId);
    });

    // Ended event: hold bar at 100% for 150ms, then fade out (250ms) before cleanup
    audio.addEventListener('ended', () => {
      if (activeItem.isStopped) return;
      this.onEnd(soundId);

      activeItem.endTimeoutId = setTimeout(() => {
        activeItem.endTimeoutId = null;
        this.cleanup(soundId);
      }, 450);
    });

    audio.addEventListener('error', (err) => {
      console.error('Audio playback error:', err);
      this.onStop(soundId);
      this.cleanup(soundId);
    });

    audio.play().catch((err) => {
      if (!activeItem.isStopped) {
        console.warn('Audio playback prevented or failed:', err);
      }
      this.onStop(soundId);
      this.cleanup(soundId);
    });
  }

  stop(soundId) {
    const item = this.activeAudios.get(soundId);
    if (item) {
      item.isStopped = true;
      if (item.endTimeoutId) {
        clearTimeout(item.endTimeoutId);
        item.endTimeoutId = null;
      }
      try {
        item.audio.pause();
        item.audio.removeAttribute('src');
        item.audio.load();
      } catch (e) {}
      this.onStop(soundId);
      this.cleanup(soundId);
    }
  }

  toggleLoop(sound) {
    const soundId = sound.id;
    const item = this.activeAudios.get(soundId);

    if (!item) {
      // Not playing: start playing directly with loop enabled
      this.play(sound, true);
      return { isPlaying: true, isLooping: true };
    }

    // Already playing: toggle loop state
    const newLoop = !item.isLooping;
    item.isLooping = newLoop;
    item.audio.loop = newLoop;
    this.onLoopToggle(soundId, newLoop);
    this.onUpdate(soundId, { isPlaying: true, isLooping: newLoop });
    return { isPlaying: true, isLooping: newLoop };
  }

  cleanup(soundId) {
    const item = this.activeAudios.get(soundId);
    if (item) {
      item.isStopped = true;
      if (item.endTimeoutId) {
        clearTimeout(item.endTimeoutId);
        item.endTimeoutId = null;
      }
      try {
        item.audio.pause();
      } catch (e) {}
      this.activeAudios.delete(soundId);
    }
    this.onUpdate(soundId, { isPlaying: false, isLooping: false });
  }

  stopAll() {
    const items = Array.from(this.activeAudios.values());
    items.forEach((item) => {
      item.isStopped = true;
      if (item.endTimeoutId) {
        clearTimeout(item.endTimeoutId);
        item.endTimeoutId = null;
      }
      try {
        item.audio.pause();
        item.audio.removeAttribute('src');
        item.audio.load();
      } catch (e) {}
    });
    const ids = Array.from(this.activeAudios.keys());
    this.activeAudios.clear();
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
