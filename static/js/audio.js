/**
 * Audio Engine for Soundboard
 * Handles polyphonic playback via Voice Pooling (Rapid Trigger), LRU memory management,
 * volume/mute control, loop toggle, and CSS-driven progress lifecycle.
 */
class AudioManager {
  constructor(options = {}) {
    this.masterVolume = options.volume ?? 0.8;
    this.isMuted = Boolean(options.muted);
    this.allowOverlap = options.allowOverlap ?? true;
    this.maxVoicesPerSound = options.maxVoicesPerSound ?? 8;
    this.maxCachedSounds = options.audioCacheSize ?? options.maxCachedSounds ?? 30;

    this.onUpdate = options.onUpdate || (() => {});
    this.onPlay = options.onPlay || (() => {});
    this.onEnd = options.onEnd || (() => {});
    this.onStop = options.onStop || (() => {});
    this.onStopAll = options.onStopAll || (() => {});
    this.onLoopToggle = options.onLoopToggle || (() => {});
    this.onLoopCycle = options.onLoopCycle || (() => {});

    // soundId -> { sound, voices: Array<voice>, lastUsed: number }
    this.soundPools = new Map();
    // soundId -> Set of active voice items
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

  setOverlap(allow) {
    this.setAllowOverlap(allow);
  }

  syncVolumes() {
    const effective = this.isMuted ? 0 : this.masterVolume;
    this.soundPools.forEach((pool) => {
      pool.voices.forEach((voice) => {
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
      if (v.isLooping && !v.isStopped && v.isPlaying) return true;
    }
    return false;
  }

  touchPool(sound) {
    const soundId = sound.id;
    let pool = this.soundPools.get(soundId);

    // If sound URL changed (e.g. updated mtime timestamp after rescan), reset pool
    if (pool && pool.sound.sound_url !== sound.sound_url) {
      this.evictSound(soundId);
      pool = null;
    }

    if (pool) {
      pool.lastUsed = Date.now();
      return pool;
    }

    // Enforce LRU cache capacity before adding new sound pool
    this.enforceLRUCapacity();

    pool = {
      sound,
      voices: [],
      lastUsed: Date.now()
    };
    this.soundPools.set(soundId, pool);
    return pool;
  }

  enforceLRUCapacity() {
    if (this.soundPools.size < this.maxCachedSounds) {
      return;
    }

    // Prefer evicting the least recently used sound that is not currently playing
    let oldestIdleId = null;
    let oldestIdleTime = Infinity;

    let oldestAnyId = null;
    let oldestAnyTime = Infinity;

    for (const [id, pool] of this.soundPools.entries()) {
      if (pool.lastUsed < oldestAnyTime) {
        oldestAnyTime = pool.lastUsed;
        oldestAnyId = id;
      }
      if (!this.isPlaying(id) && pool.lastUsed < oldestIdleTime) {
        oldestIdleTime = pool.lastUsed;
        oldestIdleId = id;
      }
    }

    const evictId = oldestIdleId || oldestAnyId;
    if (evictId) {
      this.evictSound(evictId);
    }
  }

  evictSound(soundId) {
    const pool = this.soundPools.get(soundId);
    if (!pool) return;

    pool.voices.forEach((voice) => {
      if (voice.endTimeoutId) {
        clearTimeout(voice.endTimeoutId);
        voice.endTimeoutId = null;
      }
      voice.isStopped = true;
      voice.isPlaying = false;
      try {
        voice.audio.pause();
        voice.audio.removeAttribute('src');
        voice.audio.load();
      } catch (e) {}
    });

    this.soundPools.delete(soundId);
    this.activeAudios.delete(soundId);
    this.latestVoiceIds.delete(soundId);
  }

  clearCache() {
    const soundIds = Array.from(this.soundPools.keys());
    soundIds.forEach((id) => this.evictSound(id));
  }

  createVoice(soundId, pool, startWithLoop) {
    const audio = new Audio(pool.sound.sound_url);
    audio.preload = 'auto';
    audio.loop = Boolean(startWithLoop);
    audio.volume = this.isMuted ? 0 : this.masterVolume;

    const voice = {
      id: Math.random().toString(36).slice(2) + Date.now().toString(36),
      audio,
      sound: pool.sound,
      isLooping: Boolean(startWithLoop),
      isStopped: false,
      isPlaying: true,
      endTimeoutId: null
    };

    // Attach listeners once to this pooled audio instance
    audio.addEventListener('playing', () => {
      if (voice.isStopped) return;
      const duration = audio.duration && !isNaN(audio.duration) && audio.duration > 0
        ? audio.duration
        : (pool.sound.duration && pool.sound.duration > 0 ? pool.sound.duration : 1);
      this.onPlay(soundId, { duration, isLooping: voice.isLooping });
    });

    audio.addEventListener('seeked', () => {
      if (voice.isStopped || !voice.isLooping) return;
      this.onLoopCycle(soundId);
    });

    audio.addEventListener('ended', () => {
      if (voice.isStopped) return;

      const isLatest = this.latestVoiceIds.get(soundId) === voice.id;
      if (isLatest) {
        this.onEnd(soundId);
      }

      voice.endTimeoutId = setTimeout(() => {
        voice.endTimeoutId = null;
        this.releaseVoice(soundId, voice);
      }, 450);
    });

    audio.addEventListener('error', (err) => {
      console.error('Audio playback error:', err);
      this.releaseVoice(soundId, voice);
    });

    pool.voices.push(voice);
    return voice;
  }

  acquireVoice(sound, startWithLoop) {
    const soundId = sound.id;
    const pool = this.touchPool(sound);

    // 1. Look for an idle voice already buffered in this sound's pool
    for (const v of pool.voices) {
      if (!v.isPlaying && !v.endTimeoutId) {
        v.id = Math.random().toString(36).slice(2) + Date.now().toString(36);
        v.isStopped = false;
        v.isPlaying = true;
        v.isLooping = Boolean(startWithLoop);
        v.audio.loop = Boolean(startWithLoop);
        v.audio.volume = this.isMuted ? 0 : this.masterVolume;
        try {
          v.audio.currentTime = 0;
        } catch (e) {}
        return v;
      }
    }

    // 2. If under limit, create a new pooled voice
    if (pool.voices.length < this.maxVoicesPerSound) {
      return this.createVoice(soundId, pool, startWithLoop);
    }

    // 3. Reached max voices for this sound: recycle oldest voice in pool
    const voiceToRecycle = pool.voices[0];
    pool.voices.push(pool.voices.shift());

    if (voiceToRecycle.endTimeoutId) {
      clearTimeout(voiceToRecycle.endTimeoutId);
      voiceToRecycle.endTimeoutId = null;
    }
    voiceToRecycle.id = Math.random().toString(36).slice(2) + Date.now().toString(36);
    voiceToRecycle.isStopped = false;
    voiceToRecycle.isPlaying = true;
    voiceToRecycle.isLooping = Boolean(startWithLoop);
    voiceToRecycle.audio.loop = Boolean(startWithLoop);
    voiceToRecycle.audio.volume = this.isMuted ? 0 : this.masterVolume;
    try {
      voiceToRecycle.audio.currentTime = 0;
    } catch (e) {}
    return voiceToRecycle;
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

    let activeSet = this.activeAudios.get(soundId);
    if (!activeSet) {
      activeSet = new Set();
      this.activeAudios.set(soundId, activeSet);
    }

    const voice = this.acquireVoice(sound, startWithLoop);
    activeSet.add(voice);
    this.latestVoiceIds.set(soundId, voice.id);
    this.onUpdate(soundId, { isPlaying: true, isLooping: Boolean(startWithLoop) });

    voice.audio.play().catch((err) => {
      if (!voice.isStopped) {
        console.warn('Audio playback prevented or failed:', err);
      }
      this.releaseVoice(soundId, voice);
    });
  }

  releaseVoice(soundId, voice) {
    voice.isPlaying = false;
    if (voice.endTimeoutId) {
      clearTimeout(voice.endTimeoutId);
      voice.endTimeoutId = null;
    }
    try {
      voice.audio.pause();
    } catch (e) {}

    const activeSet = this.activeAudios.get(soundId);
    if (activeSet) {
      activeSet.delete(voice);
      if (activeSet.size === 0) {
        this.activeAudios.delete(soundId);
        this.latestVoiceIds.delete(soundId);
        this.onUpdate(soundId, { isPlaying: false, isLooping: false });
      }
    }
  }

  stop(soundId) {
    const activeSet = this.activeAudios.get(soundId);
    if (activeSet && activeSet.size > 0) {
      const voiceList = Array.from(activeSet);
      voiceList.forEach((voice) => {
        voice.isStopped = true;
        voice.isPlaying = false;
        voice.isLooping = false;
        if (voice.endTimeoutId) {
          clearTimeout(voice.endTimeoutId);
          voice.endTimeoutId = null;
        }
        try {
          voice.audio.pause();
          voice.audio.currentTime = 0;
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
    const ids = Array.from(this.activeAudios.keys());
    this.activeAudios.forEach((activeSet) => {
      activeSet.forEach((voice) => {
        voice.isStopped = true;
        voice.isPlaying = false;
        voice.isLooping = false;
        if (voice.endTimeoutId) {
          clearTimeout(voice.endTimeoutId);
          voice.endTimeoutId = null;
        }
        try {
          voice.audio.pause();
          voice.audio.currentTime = 0;
        } catch (e) {}
      });
    });
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
