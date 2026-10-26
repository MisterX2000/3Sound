(function () {
  function soundboardComponent() {
    return {
      sounds: [],
      folders: {},
      categories: ['All'],
      activeCategory: 'All',
      currentFolder: '',
      viewMode: 'flat',
      searchQuery: '',
      masterVolume: 0.8,
      isMuted: false,
      allowOverlap: true,
      isLoading: true,
      isRescanning: false,
      toastMessage: null,
      toastTimeout: null,

      // Reactive playback states: soundId arrays for instant reactivity
      playingIds: [],
      loopingIds: [],
      progressMap: {},
      playback: {},
      audio: null,

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

      // Initialize audio engine
      this.audio = new AudioManager({
        volume: this.masterVolume,
        muted: this.isMuted,
        allowOverlap: this.allowOverlap,
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

          this.progressMap = { ...this.progressMap, [soundId]: state.progress || 0 };
          this.playback = { ...this.playback, [soundId]: state };
        }
      });

      // Parse initial URL hash
      this.syncFromHash(window.location.hash);
      window.addEventListener('hashchange', () => {
        this.syncFromHash(window.location.hash);
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

      // Load sounds from API
      this.loadSounds();
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
      } else if (params.has('category')) {
        this.viewMode = 'flat';
        this.activeCategory = params.get('category') || 'All';
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
      localStorage.setItem('soundboard_view_mode', mode);
      this.updateHash();
    },

    selectCategory(cat) {
      this.activeCategory = cat || 'All';
      this.updateHash();
    },

    openFolder(path) {
      this.currentFolder = path || '';
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
      }
    },

    // Instant click: play or stop (zero latency)
    handleSoundCardClick(sound, event) {
      if (event && event.currentTarget && typeof event.currentTarget.blur === 'function') {
        event.currentTarget.blur();
      }
      if (this.isPlaying(sound.id)) {
        this.playingIds = this.playingIds.filter((id) => id !== sound.id);
        this.loopingIds = this.loopingIds.filter((id) => id !== sound.id);
        this.audio.stop(sound.id);
      } else {
        if (!this.allowOverlap) {
          this.playingIds = [sound.id];
          this.loopingIds = [];
        } else if (!this.playingIds.includes(sound.id)) {
          this.playingIds = [...this.playingIds, sound.id];
        }
        this.audio.play(sound, false);
      }
    },

    toggleSoundLoop(sound) {
      const res = this.audio.toggleLoop(sound);
      if (res && res.isPlaying) {
        if (!this.playingIds.includes(sound.id)) {
          this.playingIds = this.allowOverlap ? [...this.playingIds, sound.id] : [sound.id];
        }
      }
      if (res && res.isLooping) {
        if (!this.loopingIds.includes(sound.id)) {
          this.loopingIds = [...this.loopingIds, sound.id];
        }
        this.showToast(`🔁 Looping enabled: ${sound.title}`);
      } else {
        this.loopingIds = this.loopingIds.filter((id) => id !== sound.id);
        this.showToast(`Loop disabled: ${sound.title}`);
      }
    },

    stopAllSounds() {
      this.playingIds = [];
      this.loopingIds = [];
      this.progressMap = {};
      this.playback = {};
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

    getProgress(soundId) {
      return this.progressMap[soundId] || 0;
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
      const counts = { All: this.sounds.length };
      this.sounds.forEach((s) => {
        counts[s.category] = (counts[s.category] || 0) + 1;
      });
      return counts;
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

    get flatCategoryGroups() {
      const filtered = this.filteredFlatSounds;
      const groups = {};
      filtered.forEach((sound) => {
        if (!groups[sound.category]) groups[sound.category] = [];
        groups[sound.category].push(sound);
      });
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
      return subs.filter((f) => {
        const name = (f.name || '').toLowerCase();
        const path = (f.path || '').toLowerCase();
        if (name.includes(query) || path.includes(query)) {
          return true;
        }
        const fPath = f.path || '';
        const prefix = fPath ? `${fPath}/` : '';
        return this.sounds.some(
          (s) =>
            (s.folder === fPath || (fPath && (s.folder || '').startsWith(prefix))) &&
            ((s.title && s.title.toLowerCase().includes(query)) ||
              (s.name && s.name.toLowerCase().includes(query)) ||
              (s.filename && s.filename.toLowerCase().includes(query)))
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
      this.updateHash();
    },

    jumpToFolder(folderPath) {
      this.viewMode = 'folder';
      this.currentFolder = folderPath || '';
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
