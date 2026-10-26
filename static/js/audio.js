/**
 * Audio Engine for Soundboard
 * Handles playback, volume/mute control, loop toggle, and native timeupdate tracking.
 */
class AudioManager {
  constructor(options = {}) {
    this.masterVolume = options.volume ?? 0.8;
    this.isMuted = Boolean(options.muted);
    this.allowOverlap = options.allowOverlap ?? true;
    this.onUpdate = options.onUpdate || (() => {});

    // soundId -> { audio, endTimeoutId, sound, isLooping, progress }
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
      progress: 0,
      isStopped: false
    };

    // Register active audio immediately to avoid race conditions with stop/stopAll
    this.activeAudios.set(soundId, activeItem);
    this.onUpdate(soundId, { isPlaying: true, isLooping: activeItem.isLooping, progress: 0 });

    // Native timeupdate listener with smooth progress calculation
    audio.addEventListener('timeupdate', () => {
      if (!activeItem.isStopped && audio.duration && audio.duration > 0) {
        const pct = Math.min(100, Math.max(0, (audio.currentTime / audio.duration) * 100));
        activeItem.progress = pct;
        this.onUpdate(soundId, { isPlaying: true, isLooping: activeItem.isLooping, progress: pct });
      }
    });

    // Ended event: ensure bar completes to 100%, hold for 350ms before reset
    audio.addEventListener('ended', () => {
      if (activeItem.isStopped) return;
      activeItem.progress = 100;
      this.onUpdate(soundId, { isPlaying: true, isLooping: false, progress: 100 });

      activeItem.endTimeoutId = setTimeout(() => {
        activeItem.endTimeoutId = null;
        this.cleanup(soundId);
      }, 350);
    });

    audio.addEventListener('error', (err) => {
      console.error('Audio playback error:', err);
      this.cleanup(soundId);
    });

    audio.play().catch((err) => {
      if (!activeItem.isStopped) {
        console.warn('Audio playback prevented or failed:', err);
      }
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
        item.audio.currentTime = 0;
      } catch (e) {}
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
    this.onUpdate(soundId, { isPlaying: true, isLooping: newLoop, progress: item.progress });
    return { isPlaying: true, isLooping: newLoop };
  }

  cleanup(soundId) {
    const item = this.activeAudios.get(soundId);
    if (item) {
      if (item.endTimeoutId) {
        clearTimeout(item.endTimeoutId);
        item.endTimeoutId = null;
      }
      this.activeAudios.delete(soundId);
    }
    this.onUpdate(soundId, { isPlaying: false, isLooping: false, progress: 0 });
  }

  stopAll() {
    const ids = Array.from(this.activeAudios.keys());
    ids.forEach((id) => this.stop(id));
    this.activeAudios.clear();
  }
}

if (typeof window !== 'undefined') {
  window.AudioManager = AudioManager;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AudioManager };
}
