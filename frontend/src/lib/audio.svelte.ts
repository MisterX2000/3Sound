import type { Sound } from '../types';

export interface VoiceItem {
  id: string;
  audio: HTMLAudioElement;
  onEnded: () => void;
  endTimeoutId?: number | null;
}

export class AudioState {
  masterVolume = $state(0.8);
  isMuted = $state(false);
  allowOverlap = $state(true);
  playingIds = $state<string[]>([]);
  loopingIds = $state<string[]>([]);

  // Internal voice pooling structures
  private soundPools = new Map<string, { sound: Sound; voices: VoiceItem[]; lastUsed: number }>();
  private activeAudios = new Map<string, Set<VoiceItem>>();
  private latestVoiceIds = new Map<string, string>();
  private maxCachedSounds = 30;
  private maxVoicesPerSound = 8;

  // Progress animation hooks
  onPlayProgress?: (soundId: string, duration: number, isLooping: boolean) => void;
  onLoopProgress?: (soundId: string, duration: number) => void;
  onEndProgress?: (soundId: string) => void;
  onStopProgress?: (soundId: string) => void;

  constructor() {
    this.onPlayProgress = (soundId, duration, isLooping) => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('sound-progress', { detail: { soundId, duration, type: isLooping ? 'loop' : 'play' } }));
      }
    };
    this.onLoopProgress = (soundId, duration) => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('sound-progress', { detail: { soundId, duration, type: 'loop' } }));
      }
    };
    this.onEndProgress = (soundId) => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('sound-progress', { detail: { soundId, duration: 0, type: 'end' } }));
      }
    };
    this.onStopProgress = (soundId) => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('sound-progress', { detail: { soundId, duration: 0, type: 'stop' } }));
      }
    };

    // Hydrate saved audio settings from localStorage
    if (typeof window !== 'undefined') {
      const savedVol = localStorage.getItem('soundboard_volume');
      if (savedVol !== null) {
        const v = parseFloat(savedVol);
        if (!isNaN(v) && v >= 0 && v <= 1) this.masterVolume = v;
      }
      const savedMute = localStorage.getItem('soundboard_muted');
      if (savedMute !== null) this.isMuted = savedMute === 'true';
      const savedOverlap = localStorage.getItem('soundboard_overlap');
      if (savedOverlap !== null) this.allowOverlap = savedOverlap === 'true';
    }
  }

  setVolume(vol: number) {
    this.masterVolume = Math.max(0, Math.min(1, vol));
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('soundboard_volume', String(this.masterVolume));
    }
    this.syncVolumes();
  }

  setMuted(muted: boolean) {
    this.isMuted = muted;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('soundboard_muted', String(this.isMuted));
    }
    this.syncVolumes();
  }

  toggleMute() {
    this.setMuted(!this.isMuted);
  }

  setOverlap(overlap: boolean) {
    this.allowOverlap = overlap;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('soundboard_overlap', String(this.allowOverlap));
    }
  }

  toggleOverlap() {
    this.setOverlap(!this.allowOverlap);
  }

  applyConfigDefaults(cfg: { default_volume?: number; default_muted?: boolean; default_allow_overlap?: boolean }) {
    if (typeof window === 'undefined') return;

    if (localStorage.getItem('soundboard_volume') === null && typeof cfg.default_volume === 'number') {
      this.masterVolume = Math.max(0, Math.min(1, cfg.default_volume / 100));
      this.syncVolumes();
    }
    if (localStorage.getItem('soundboard_muted') === null && typeof cfg.default_muted === 'boolean') {
      this.isMuted = cfg.default_muted;
      this.syncVolumes();
    }
    if (localStorage.getItem('soundboard_overlap') === null && typeof cfg.default_allow_overlap === 'boolean') {
      this.allowOverlap = cfg.default_allow_overlap;
    }
  }

  setCacheSize(size: number) {
    if (size > 0) this.maxCachedSounds = size;
  }

  isPlaying(soundId: string): boolean {
    return this.playingIds.includes(soundId);
  }

  isLooping(soundId: string): boolean {
    return this.loopingIds.includes(soundId);
  }

  private syncVolumes() {
    const effective = this.isMuted ? 0 : this.masterVolume;
    for (const pool of this.soundPools.values()) {
      for (const voice of pool.voices) {
        voice.audio.volume = effective;
      }
    }
  }

  private acquireVoice(sound: Sound): VoiceItem {
    let pool = this.soundPools.get(sound.id);
    if (!pool) {
      this.evictIfNeeded();
      pool = { sound, voices: [], lastUsed: Date.now() };
      this.soundPools.set(sound.id, pool);
    }
    pool.lastUsed = Date.now();

    const activeSet = this.activeAudios.get(sound.id);
    // Find an idle voice
    for (const voice of pool.voices) {
      if (!activeSet || !activeSet.has(voice)) {
        voice.audio.currentTime = 0;
        return voice;
      }
    }

    // Allocate a new voice if limit not reached
    if (pool.voices.length < this.maxVoicesPerSound) {
      const audio = new Audio();
      audio.preload = 'auto';
      audio.src = sound.sound_url;
      const effective = this.isMuted ? 0 : this.masterVolume;
      audio.volume = effective;

      const voiceId = `${sound.id}_v_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const voiceItem: VoiceItem = {
        id: voiceId,
        audio,
        onEnded: () => this.handleVoiceEnded(sound.id, voiceItem),
      };

      audio.addEventListener('ended', voiceItem.onEnded);
      audio.addEventListener('error', () => {
        this.releaseVoice(sound.id, voiceItem);
      });

      pool.voices.push(voiceItem);
      return voiceItem;
    }

    // Reuse oldest active voice
    const oldest = pool.voices[0];
    try {
      oldest.audio.pause();
      oldest.audio.currentTime = 0;
    } catch {}
    this.releaseVoice(sound.id, oldest);
    return oldest;
  }

  private handleVoiceEnded(soundId: string, voice: VoiceItem) {
    if (this.isLooping(soundId)) {
      try {
        voice.audio.currentTime = 0;
        voice.audio.play();
        const pool = this.soundPools.get(soundId);
        const duration = pool?.sound.duration || voice.audio.duration || 1;
        this.onLoopProgress?.(soundId, duration);
        return;
      } catch {
        // Fallback to release on error
      }
    }
    this.releaseVoice(soundId, voice);
  }

  private releaseVoice(soundId: string, voice: VoiceItem) {
    if (voice.endTimeoutId) {
      clearTimeout(voice.endTimeoutId);
      voice.endTimeoutId = null;
    }
    try {
      voice.audio.pause();
    } catch {}

    const activeSet = this.activeAudios.get(soundId);
    if (activeSet) {
      activeSet.delete(voice);
      // Robust ID matching for identity safety
      for (const item of activeSet) {
        if (item === voice || (item && item.id === voice.id)) {
          activeSet.delete(item);
          break;
        }
      }
      if (activeSet.size === 0) {
        this.activeAudios.delete(soundId);
        this.latestVoiceIds.delete(soundId);
        this.setSoundPlaying(soundId, false);
        this.setSoundLooping(soundId, false);
        this.onEndProgress?.(soundId);
      }
    }
  }

  private setSoundPlaying(soundId: string, isPlaying: boolean) {
    if (isPlaying) {
      if (!this.playingIds.includes(soundId)) {
        this.playingIds = this.allowOverlap ? [...this.playingIds, soundId] : [soundId];
      }
    } else {
      this.playingIds = this.playingIds.filter((id) => id !== soundId);
    }
  }

  private setSoundLooping(soundId: string, isLooping: boolean) {
    if (isLooping) {
      if (!this.loopingIds.includes(soundId)) {
        this.loopingIds = [...this.loopingIds, soundId];
      }
    } else {
      this.loopingIds = this.loopingIds.filter((id) => id !== soundId);
    }
  }

  private evictIfNeeded() {
    if (this.soundPools.size < this.maxCachedSounds) return;

    let oldestId: string | null = null;
    let oldestTime = Infinity;

    for (const [id, pool] of this.soundPools.entries()) {
      const isActive = this.activeAudios.has(id);
      if (!isActive && pool.lastUsed < oldestTime) {
        oldestTime = pool.lastUsed;
        oldestId = id;
      }
    }

    if (!oldestId) {
      for (const [id, pool] of this.soundPools.entries()) {
        if (pool.lastUsed < oldestTime) {
          oldestTime = pool.lastUsed;
          oldestId = id;
        }
      }
    }

    if (oldestId) {
      this.evictSound(oldestId);
    }
  }

  private evictSound(soundId: string) {
    const pool = this.soundPools.get(soundId);
    if (!pool) return;

    pool.voices.forEach((voice) => {
      if (voice.endTimeoutId) clearTimeout(voice.endTimeoutId);
      voice.audio.removeEventListener('ended', voice.onEnded);
      try {
        voice.audio.pause();
        voice.audio.src = '';
        voice.audio.load();
      } catch {}
    });

    const wasActive = this.activeAudios.has(soundId);
    this.soundPools.delete(soundId);
    this.activeAudios.delete(soundId);
    this.latestVoiceIds.delete(soundId);

    if (wasActive) {
      this.setSoundPlaying(soundId, false);
      this.setSoundLooping(soundId, false);
      this.onEndProgress?.(soundId);
    }
  }

  async play(sound: Sound) {
    if (!this.allowOverlap) {
      this.stopAll();
    }

    const voice = this.acquireVoice(sound);
    let activeSet = this.activeAudios.get(sound.id);
    if (!activeSet) {
      activeSet = new Set<VoiceItem>();
      this.activeAudios.set(sound.id, activeSet);
    }
    activeSet.add(voice);
    this.latestVoiceIds.set(sound.id, voice.id);

    const isLoop = this.isLooping(sound.id);
    this.setSoundPlaying(sound.id, true);

    try {
      voice.audio.currentTime = 0;
      await voice.audio.play();

      const duration = sound.duration || voice.audio.duration || 1;
      this.onPlayProgress?.(sound.id, duration, isLoop);

      // Duration safeguard timeout
      if (!isLoop && duration > 0) {
        if (voice.endTimeoutId) clearTimeout(voice.endTimeoutId);
        voice.endTimeoutId = window.setTimeout(() => {
          this.releaseVoice(sound.id, voice);
        }, Math.ceil(duration * 1000) + 1000);
      }
    } catch (err) {
      console.warn(`Playback failed for ${sound.title}:`, err);
      this.releaseVoice(sound.id, voice);
    }
  }

  stop(soundId: string) {
    const activeSet = this.activeAudios.get(soundId);
    if (activeSet) {
      const voices = Array.from(activeSet);
      for (const voice of voices) {
        this.releaseVoice(soundId, voice);
      }
    }
    this.setSoundPlaying(soundId, false);
    this.setSoundLooping(soundId, false);
    this.onStopProgress?.(soundId);
  }

  stopAll() {
    const ids = Array.from(this.activeAudios.keys());
    for (const id of ids) {
      this.stop(id);
    }
    this.playingIds = [];
    this.loopingIds = [];
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('sound-progress', { detail: { soundId: 'all', duration: 0, type: 'stop' } }));
    }
  }

  toggleLoop(sound: Sound) {
    const isCurrentlyLooping = this.isLooping(sound.id);
    const newLoop = !isCurrentlyLooping;
    this.setSoundLooping(sound.id, newLoop);

    const pool = this.soundPools.get(sound.id);
    if (pool) {
      for (const voice of pool.voices) {
        voice.audio.loop = false;
      }
    }

    if (newLoop && !this.isPlaying(sound.id)) {
      this.play(sound);
    }
  }
}

export const audio = new AudioState();
