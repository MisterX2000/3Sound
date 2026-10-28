(function () {
  function soundboardComponent() {
    const serverConfig = (typeof window !== 'undefined' && window.__SOUNDBOARD_CONFIG__) || {};
    const defaultView = serverConfig.default_view_mode === 'folder' ? 'folder' : 'flat';
    const defaultVol = typeof serverConfig.default_volume === 'number'
      ? Math.max(0, Math.min(1, serverConfig.default_volume / 100))
      : 0.8;
    const defaultOverlap = serverConfig.default_allow_overlap !== false;
    const defaultMuted = serverConfig.default_muted === true;
    const appTitle = serverConfig.app_title || 'Soundboard';

    return {
      sounds: [],
      folders: {},
      categories: ['All'],
      activeCategory: 'All',
      currentFolder: '',
      viewMode: defaultView,
      searchQuery: '',
      masterVolume: defaultVol,
      isMuted: defaultMuted,
      allowOverlap: defaultOverlap,
      appTitle: appTitle,
      isLoading: true,
      isRescanning: false,
      appVersion: '',
      toastMessage: null,
      toastTimeout: null,

      // Progressive rendering limit for large libraries
      renderLimit: 80,
      categoryCountsMap: { All: 0 },

      // Reactive playback states: soundId arrays for instant reactivity
      playingIds: [],
      loopingIds: [],
      audio: null,
      infiniteScrollObserver: null,

    init() {
      // Restore persisted settings
      const savedViewMode = localStorage.getItem('soundboard_view_mode');
      if (savedViewMode === 'flat' || savedViewMode === 'folder') {
        this.viewMode = savedViewMode;
      }

      const savedVol = localStorage.getItem('soundboard_volume');
      if (savedVol !== null) {
        const parsed = parseFloat(savedVol);
        if (!isNaN(parsed) && parsed >= 0 && parsed <= 1) {
          this.masterVolume = parsed;
        }
      }

      const savedMute = localStorage.getItem('soundboard_muted');
      if (savedMute !== null) {
        this.isMuted = savedMute === 'true';
      }

      const savedOverlap = localStorage.getItem('soundboard_overlap');
      if (savedOverlap !== null) {
        this.allowOverlap = savedOverlap === 'true';
      }

      // Initialize audio engine with GPU-accelerated CSS progress bar animation
      this.audio = new AudioManager({
        volume: this.masterVolume,
        muted: this.isMuted,
        allowOverlap: this.allowOverlap,
        onPlay: (soundId, { duration, isLooping }) => {
          this.triggerProgressBarPlay(soundId, duration, isLooping);
        },
        onLoopCycle: (soundId) => {
          this.triggerProgressBarLoopCycle(soundId);
        },
        onLoopToggle: (soundId, isLooping) => {
          this.triggerProgressBarLoopToggle(soundId, isLooping);
        },
        onEnd: (soundId) => {
          this.triggerProgressBarEnd(soundId);
        },
        onStop: (soundId) => {
          this.triggerProgressBarStop(soundId);
        },
        onStopAll: () => {
          this.triggerProgressBarStopAll();
        },
        onUpdate: (soundId, state) => {
          if (state.isPlaying) {
            if (!this.playingIds.includes(soundId)) {
              this.playingIds = this.allowOverlap ? [...this.playingIds, soundId] : [soundId];
            }
          } else {
            this.playingIds = this.playingIds.filter((id) => id !== soundId);
          }

          if (state.isLooping) {
            if (!this.loopingIds.includes(soundId)) {
              this.loopingIds = [...this.loopingIds, soundId];
            }
          } else {
            this.loopingIds = this.loopingIds.filter((id) => id !== soundId);
          }
        }
      });

      // Parse initial URL hash
      this.syncFromHash(window.location.hash);
      window.addEventListener('hashchange', () => {
        this.syncFromHash(window.location.hash);
      });

      // Reset render limit when search changes
      this.$watch('searchQuery', () => {
        this.renderLimit = 80;
      });

      // Global keyboard shortcuts
      window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.stopAllSounds();
        } else if (
          e.key === '/' &&
          document.activeElement?.tagName !== 'INPUT' &&
          document.activeElement?.tagName !== 'TEXTAREA'
        ) {
          e.preventDefault();
          const searchInput = document.getElementById('search-input');
          if (searchInput) {
            searchInput.focus();
            searchInput.select();
          }
        }
      });

      // Register PWA service worker
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch((err) => {
          console.warn('Service worker registration failed:', err);
        });
      }

      // Setup infinite scroll observer
      this.setupInfiniteScroll();

      // Load sounds from API
      this.loadSounds();
    },

    setupInfiniteScroll() {
      if (typeof IntersectionObserver === 'undefined') return;
      this.infiniteScrollObserver = new IntersectionObserver(
        (entries) => {
          if (entries.some((entry) => entry.isIntersecting)) {
            this.loadMore();
          }
        },
        { rootMargin: '300px' }
      );

      this.$nextTick(() => {
        const sentinel = document.getElementById('infinite-scroll-sentinel');
        if (sentinel && this.infiniteScrollObserver) {
          this.infiniteScrollObserver.observe(sentinel);
        }
      });
    },

    loadMore() {
      if (this.hasMoreFlatSounds) {
        this.renderLimit += 60;
      }
    },

    showToast(msg, duration = 2500) {
      this.toastMessage = msg;
      if (this.toastTimeout) clearTimeout(this.toastTimeout);
      this.toastTimeout = setTimeout(() => {
        this.toastMessage = null;
      }, duration);
    },

    syncFromHash(hashStr) {
      if (!hashStr || !hashStr.startsWith('#')) return;
      const clean = hashStr.substring(1);
      const params = new URLSearchParams(clean);

      if (params.has('folder')) {
        this.viewMode = 'folder';
        this.currentFolder = params.get('folder') || '';
        this.renderLimit = 80;
      } else if (params.has('category')) {
        this.viewMode = 'flat';
        this.activeCategory = params.get('category') || 'All';
        this.renderLimit = 80;
      }
    },

    updateHash() {
      let targetHash = '';
      if (this.viewMode === 'folder') {
        targetHash = this.currentFolder ? `#folder=${encodeURIComponent(this.currentFolder)}` : '#folder=';
      } else {
        targetHash =
          this.activeCategory && this.activeCategory !== 'All'
            ? `#category=${encodeURIComponent(this.activeCategory)}`
            : '#category=All';
      }
      if (window.location.hash !== targetHash) {
        window.history.pushState(null, '', targetHash);
      }
    },

    setViewMode(mode) {
      this.viewMode = mode;
      this.renderLimit = 80;
      localStorage.setItem('soundboard_view_mode', mode);
      this.updateHash();
      this.$nextTick(() => {
        const sentinel = document.getElementById('infinite-scroll-sentinel');
        if (sentinel && this.infiniteScrollObserver) {
          this.infiniteScrollObserver.observe(sentinel);
        }
      });
    },

    selectCategory(cat) {
      this.activeCategory = cat || 'All';
      this.renderLimit = 80;
      this.updateHash();
    },

    openFolder(path) {
      this.currentFolder = path || '';
      this.renderLimit = 80;
      this.updateHash();
    },

    setVolume(val) {
      const vol = parseFloat(val);
      this.masterVolume = vol;
      localStorage.setItem('soundboard_volume', String(vol));
      this.audio.setVolume(vol);
    },

    toggleMute() {
      this.isMuted = !this.isMuted;
      localStorage.setItem('soundboard_muted', String(this.isMuted));
      this.audio.setMuted(this.isMuted);
    },

    toggleOverlap(forcedVal = null) {
      if (typeof forcedVal === 'boolean') {
        this.allowOverlap = forcedVal;
      } else {
        this.allowOverlap = !this.allowOverlap;
      }
      localStorage.setItem('soundboard_overlap', String(this.allowOverlap));
      this.audio.setAllowOverlap(this.allowOverlap);
      if (!this.allowOverlap && this.playingIds.length > 1) {
        const keepId = this.playingIds[this.playingIds.length - 1];
        const toStop = this.playingIds.slice(0, -1);
        toStop.forEach((id) => this.audio.stop(id));
        this.playingIds = [keepId];
      }
    },

    async loadSounds(forceReload = false) {
      this.isRescanning = forceReload;
      try {
        const url = forceReload ? '/api/sounds?reload=true' : '/api/sounds';
        const res = await fetch(url);
        const data = await res.json();

        this.sounds = data.sounds || [];
        this.categories = ['All', ...(data.categories || [])];
        this.folders = data.folders || {};
        if (data.version) {
          this.appVersion = data.version;
        }

        if (data.config) {
          if (data.config.app_title) {
            this.appTitle = data.config.app_title;
            document.title = data.config.app_title;
          }
          if (!localStorage.getItem('soundboard_view_mode') && data.config.default_view_mode) {
            this.viewMode = data.config.default_view_mode;
          }
          if (localStorage.getItem('soundboard_volume') === null && typeof data.config.default_volume === 'number') {
            const vol = Math.max(0, Math.min(1, data.config.default_volume / 100));
            this.masterVolume = vol;
            if (this.audio) this.audio.setVolume(vol);
          }
          if (localStorage.getItem('soundboard_overlap') === null && typeof data.config.default_allow_overlap === 'boolean') {
            this.allowOverlap = data.config.default_allow_overlap;
            if (this.audio) this.audio.setOverlap(this.allowOverlap);
          }
          if (localStorage.getItem('soundboard_muted') === null && typeof data.config.default_muted === 'boolean') {
            this.isMuted = data.config.default_muted;
            if (this.audio) this.audio.setMuted(this.isMuted);
          }
        }

        // Precompute category counts map once in O(N)
        const counts = { All: this.sounds.length };
        for (let i = 0; i < this.sounds.length; i++) {
          const c = this.sounds[i].category;
          counts[c] = (counts[c] || 0) + 1;
        }
        this.categoryCountsMap = counts;

        if (this.currentFolder && !this.folders[this.currentFolder]) {
          this.currentFolder = '';
        }
        if (this.activeCategory !== 'All' && !this.categories.includes(this.activeCategory)) {
          this.activeCategory = 'All';
        }

        if (forceReload) {
          this.showToast(`Filesystem rescanned: ${this.sounds.length} sounds loaded`);
        }
      } catch (err) {
        console.error('Failed to load sounds:', err);
        this.showToast('Error loading sounds');
      } finally {
        this.isLoading = false;
        this.isRescanning = false;
        this.$nextTick(() => {
          const sentinel = document.getElementById('infinite-scroll-sentinel');
          if (sentinel && this.infiniteScrollObserver) {
            this.infiniteScrollObserver.observe(sentinel);
          }
        });
      }
    },

    // Stop all voices of a specific sound
    stopSound(soundId) {
      this.playingIds = this.playingIds.filter((id) => id !== soundId);
      this.loopingIds = this.loopingIds.filter((id) => id !== soundId);
      if (this.audio) {
        this.audio.stop(soundId);
      }
    },

    // Instant click: rapid trigger (polyphony) in overlap mode, or solo toggle
    handleSoundCardClick(sound, event) {
      if (event && event.currentTarget && typeof event.currentTarget.blur === 'function') {
        event.currentTarget.blur();
      }

      // If active looping sound, clicking the card stops it
      if (this.isLooping(sound.id)) {
        this.stopSound(sound.id);
        return;
      }

      // If Solo mode (overlap disabled) and already playing: stop it
      if (!this.allowOverlap && this.isPlaying(sound.id)) {
        this.stopSound(sound.id);
        return;
      }

      // Rapid trigger (overlap enabled) or initial play
      if (!this.allowOverlap) {
        this.playingIds = [sound.id];
        this.loopingIds = [];
      } else if (!this.playingIds.includes(sound.id)) {
        this.playingIds = [...this.playingIds, sound.id];
      }
      this.audio.play(sound, false);
    },

    toggleSoundLoop(sound) {
      const res = this.audio.toggleLoop(sound);
      if (res && res.isLooping) {
        if (!this.playingIds.includes(sound.id)) {
          this.playingIds = this.allowOverlap ? [...this.playingIds, sound.id] : [sound.id];
        }
        if (!this.loopingIds.includes(sound.id)) {
          this.loopingIds = [...this.loopingIds, sound.id];
        }
        this.showToast(`🔁 Looping enabled: ${sound.title}`);
      } else {
        this.playingIds = this.playingIds.filter((id) => id !== sound.id);
        this.loopingIds = this.loopingIds.filter((id) => id !== sound.id);
        this.showToast(`Loop stopped: ${sound.title}`);
      }
    },

    getSafeBars(soundId) {
      if (typeof document === 'undefined') return [];
      const safeId = typeof CSS !== 'undefined' && CSS.escape ? CSS.escape(soundId) : soundId.replace(/["\\]/g, '\\$&');
      return document.querySelectorAll(`[data-progress-id="${safeId}"]`);
    },

    triggerProgressBarPlay(soundId, duration, isLooping) {
      this.getSafeBars(soundId).forEach((bar) => {
        if (bar._fadeTimeout) {
          clearTimeout(bar._fadeTimeout);
          bar._fadeTimeout = null;
        }
        bar.style.transition = 'none';
        bar.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
        bar.style.transform = 'scaleX(0)';
        bar.style.opacity = '';
        // Force reflow to restart CSS animation cleanly
        void bar.offsetWidth;
        bar.style.transition = '';
        bar.style.setProperty('--sound-duration', `${duration}s`);
        bar.classList.add('is-animating');
        if (isLooping) {
          bar.classList.add('is-looping');
        }
      });
    },

    triggerProgressBarLoopToggle(soundId, isLooping) {
      this.getSafeBars(soundId).forEach((bar) => {
        if (isLooping) {
          bar.classList.add('is-looping');
        } else {
          bar.classList.remove('is-looping');
        }
      });
    },

    triggerProgressBarLoopCycle(soundId) {
      this.getSafeBars(soundId).forEach((bar) => {
        bar.classList.remove('is-animating');
        void bar.offsetWidth;
        bar.classList.add('is-animating', 'is-looping');
      });
    },

    triggerProgressBarEnd(soundId) {
      this.getSafeBars(soundId).forEach((bar) => {
        if (bar._fadeTimeout) clearTimeout(bar._fadeTimeout);
        // Hold full bar for 150ms before smoothly fading out over 250ms
        bar._fadeTimeout = setTimeout(() => {
          bar.classList.add('is-fading');
          bar._fadeTimeout = setTimeout(() => {
            bar.style.transition = 'none';
            bar.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
            bar.style.transform = 'scaleX(0)';
            bar.style.opacity = '';
            void bar.offsetWidth;
            bar.style.transition = '';
            bar._fadeTimeout = null;
          }, 270);
        }, 150);
      });
    },

    triggerProgressBarStop(soundId) {
      this.getSafeBars(soundId).forEach((bar) => {
        if (bar._fadeTimeout) clearTimeout(bar._fadeTimeout);
        // Pause in place immediately and fade out over 250ms without backward rewind
        bar.classList.add('is-paused', 'is-fading');
        bar._fadeTimeout = setTimeout(() => {
          bar.style.transition = 'none';
          bar.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
          bar.style.transform = 'scaleX(0)';
          bar.style.opacity = '';
          void bar.offsetWidth;
          bar.style.transition = '';
          bar._fadeTimeout = null;
        }, 270);
      });
    },

    triggerProgressBarStopAll() {
      if (typeof document === 'undefined') return;
      document.querySelectorAll('.progress-bar.is-animating, .progress-bar.is-fading').forEach((bar) => {
        if (bar._fadeTimeout) clearTimeout(bar._fadeTimeout);
        bar.classList.add('is-paused', 'is-fading');
        bar._fadeTimeout = setTimeout(() => {
          bar.style.transition = 'none';
          bar.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
          bar.style.transform = 'scaleX(0)';
          bar.style.opacity = '';
          void bar.offsetWidth;
          bar.style.transition = '';
          bar._fadeTimeout = null;
        }, 270);
      });
    },

    stopAllSounds() {
      this.playingIds = [];
      this.loopingIds = [];
      if (this.audio) {
        this.audio.stopAll();
      }
      if (typeof document !== 'undefined') {
        if (document.activeElement && typeof document.activeElement.blur === 'function') {
          document.activeElement.blur();
        }
        document.querySelectorAll('.sound-card').forEach((el) => {
          if (typeof el.blur === 'function') el.blur();
        });
      }
    },

    isPlaying(soundId) {
      return this.playingIds.includes(soundId);
    },

    isLooping(soundId) {
      return this.loopingIds.includes(soundId);
    },

    formatTime(seconds) {
      if (!seconds || seconds <= 0) return '0:00';
      const totalSecs = Math.round(seconds);
      const mins = Math.floor(totalSecs / 60);
      const secs = totalSecs % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },

    // --- Computed getters ---
    get categoryCounts() {
      return this.categoryCountsMap;
    },

    get filteredFlatSounds() {
      const query = this.searchQuery.toLowerCase().trim();
      return this.sounds.filter((s) => {
        const matchesCategory = this.activeCategory === 'All' || s.category === this.activeCategory;
        const matchesQuery =
          !query ||
          s.title.toLowerCase().includes(query) ||
          s.name.toLowerCase().includes(query) ||
          s.category.toLowerCase().includes(query) ||
          s.filename.toLowerCase().includes(query);
        return matchesCategory && matchesQuery;
      });
    },

    get hasMoreFlatSounds() {
      return this.filteredFlatSounds.length > this.renderLimit;
    },

    get flatCategoryGroups() {
      const filtered = this.filteredFlatSounds;
      const limit = this.renderLimit;
      const groups = {};
      let count = 0;

      for (let i = 0; i < filtered.length; i++) {
        if (count >= limit) break;
        const s = filtered[i];
        if (!groups[s.category]) groups[s.category] = [];
        groups[s.category].push(s);
        count++;
      }

      return Object.entries(groups).map(([name, soundList]) => ({
        name,
        sounds: soundList
      }));
    },

    get currentFolderObj() {
      return (
        this.folders[this.currentFolder] || {
          name: 'All Sounds',
          parent: null,
          subfolders: [],
          sound_ids: [],
          sound_count: 0,
          total_sound_count: this.sounds.length
        }
      );
    },

    get breadcrumbs() {
      if (!this.currentFolder) return [];
      const parts = this.currentFolder.split('/');
      let cumulative = '';
      return parts.map((part, index) => {
        cumulative = cumulative ? `${cumulative}/${part}` : part;
        return {
          name: part,
          path: cumulative,
          isLast: index === parts.length - 1
        };
      });
    },

    get displayedSubfolders() {
      const query = this.searchQuery.toLowerCase().trim();
      const subs = (this.currentFolderObj.subfolders || [])
        .map((p) => this.folders[p])
        .filter(Boolean);
      if (!query) return subs;
      const matchingSounds = this.globalSearchResults;
      return subs.filter((f) => {
        const name = (f.name || '').toLowerCase();
        const path = (f.path || '').toLowerCase();
        if (name.includes(query) || path.includes(query)) {
          return true;
        }
        const fPath = f.path || '';
        const prefix = fPath ? `${fPath}/` : '';
        return matchingSounds.some(
          (s) => s.folder === fPath || (fPath && (s.folder || '').startsWith(prefix))
        );
      });
    },

    get directFolderSounds() {
      const query = this.searchQuery.toLowerCase().trim();
      const list = this.sounds.filter((s) => (s.folder || '') === this.currentFolder);
      if (!query) return list;
      return list.filter(
        (s) =>
          s.title.toLowerCase().includes(query) ||
          s.name.toLowerCase().includes(query) ||
          s.filename.toLowerCase().includes(query)
      );
    },

    get globalSearchResults() {
      const query = this.searchQuery.toLowerCase().trim();
      if (!query) return [];
      return this.sounds.filter(
        (s) =>
          (s.title && s.title.toLowerCase().includes(query)) ||
          (s.name && s.name.toLowerCase().includes(query)) ||
          (s.category && s.category.toLowerCase().includes(query)) ||
          (s.filename && s.filename.toLowerCase().includes(query))
      );
    },

    get hasLocalResults() {
      if (!this.searchQuery.trim()) return true;
      if (this.viewMode === 'flat') {
        return this.filteredFlatSounds.length > 0;
      } else {
        return this.displayedSubfolders.length > 0 || this.directFolderSounds.length > 0;
      }
    },

    get showGlobalFallback() {
      return Boolean(this.searchQuery.trim() && !this.hasLocalResults && this.globalSearchResults.length > 0);
    },

    jumpToCategory(category) {
      this.activeCategory = category || 'All';
      this.renderLimit = 80;
      this.updateHash();
    },

    jumpToFolder(folderPath) {
      this.viewMode = 'folder';
      this.currentFolder = folderPath || '';
      this.renderLimit = 80;
      localStorage.setItem('soundboard_view_mode', 'folder');
      this.updateHash();
    },

    get displayedCountBadge() {
      if (this.showGlobalFallback) {
        const count = this.globalSearchResults.length;
        return `${count} global match${count === 1 ? '' : 'es'}`;
      }
      if (this.viewMode === 'flat') {
        const count = this.filteredFlatSounds.length;
        return `${count} sound${count === 1 ? '' : 's'}`;
      } else {
        const count = this.directFolderSounds.length;
        return `${count} sound${count === 1 ? '' : 's'}`;
      }
    }
  };
}

  function registerSoundboard() {
    if (typeof Alpine !== 'undefined' && typeof Alpine.data === 'function') {
      Alpine.data('soundboard', soundboardComponent);
    }
  }

  if (typeof window !== 'undefined' && typeof window.Alpine !== 'undefined') {
    registerSoundboard();
  } else {
    document.addEventListener('alpine:init', registerSoundboard);
  }
})();
