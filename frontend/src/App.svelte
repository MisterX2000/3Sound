<script lang="ts">
  import { onMount } from 'svelte';
  import type { Sound, FolderInfo, ViewMode, SoundsResponse, ClientConfig, BreadcrumbItem } from './types';
  import { audio } from './lib/audio.svelte';
  import Header from './lib/components/Header.svelte';
  import FlatView from './lib/components/FlatView.svelte';
  import FolderView from './lib/components/FolderView.svelte';
  import EmptySearch from './lib/components/EmptySearch.svelte';
  import Toast from './lib/components/Toast.svelte';
  import { Loader2 } from '@lucide/svelte';

  let isLoading = $state(true);
  let isRescanning = $state(false);
  let sounds = $state<Sound[]>([]);
  let folders = $state<Record<string, FolderInfo>>({});
  let categories = $state<string[]>(['All']);
  let activeCategory = $state('All');
  let currentFolder = $state('');
  let viewMode = $state<ViewMode>('flat');
  let searchQuery = $state('');
  let appTitle = $state('Soundboard');
  let appVersion = $state('');
  let toastMessage = $state<string | null>(null);
  let toastTimeout = $state<number | null>(null);

  let headerComponent = $state<any>(null);

  function showToast(msg: string) {
    if (toastTimeout) clearTimeout(toastTimeout);
    toastMessage = msg;
    toastTimeout = window.setTimeout(() => {
      toastMessage = null;
    }, 3000);
  }

  // Breadcrumbs calculation for Folder view
  const breadcrumbs = $derived.by<BreadcrumbItem[]>(() => {
    if (!currentFolder) return [];
    const parts = currentFolder.split('/').filter(Boolean);
    let acc = '';
    return parts.map((part, index) => {
      acc = acc ? `${acc}/${part}` : part;
      return {
        name: part,
        path: acc,
        isLast: index === parts.length - 1,
      };
    });
  });

  // Hash-based URL routing & state sync
  function syncFromHash(hash: string) {
    const raw = (hash || '').replace(/^#/, '');
    if (!raw) {
      currentFolder = '';
      activeCategory = 'All';
      searchQuery = '';
      return;
    }

    const params = new URLSearchParams(raw);
    const mode = params.get('view') as ViewMode | null;
    if (mode === 'flat' || mode === 'folder') {
      viewMode = mode;
    }

    if (params.has('folder')) {
      const f = params.get('folder') || '';
      viewMode = 'folder';
      currentFolder = f;
    } else if (params.has('category')) {
      const c = params.get('category') || 'All';
      viewMode = 'flat';
      activeCategory = c;
    }

    const q = params.get('q') || '';
    if (searchQuery !== q) {
      searchQuery = q;
    }
  }

  function buildHash(): string {
    const params = new URLSearchParams();
    if (viewMode === 'folder') {
      params.set('folder', currentFolder || '');
    } else {
      if (activeCategory !== 'All') {
        params.set('category', activeCategory);
      }
    }
    const q = searchQuery.trim();
    if (q) {
      params.set('q', q);
    }
    return '#' + params.toString();
  }

  function updateHash(replace = false) {
    if (typeof window === 'undefined') return;
    const targetHash = buildHash();
    if (window.location.hash !== targetHash) {
      if (replace) {
        window.history.replaceState(null, '', targetHash);
      } else {
        window.history.pushState(null, '', targetHash);
      }
    }
  }

  // View mode switcher with View Transitions API support
  function setViewMode(mode: ViewMode) {
    if (viewMode === mode) return;

    const applyChange = () => {
      viewMode = mode;
      localStorage.setItem('soundboard_view_mode', mode);
      updateHash(false);
    };

    if (typeof document !== 'undefined' && 'startViewTransition' in document) {
      (document as any).startViewTransition(applyChange);
    } else {
      applyChange();
    }
  }

  function selectCategory(cat: string) {
    activeCategory = cat;
    updateHash(false);
  }

  function openFolder(path: string) {
    currentFolder = path;
    updateHash(false);
  }

  function goToParentFolder() {
    const current = folders[currentFolder];
    openFolder(current?.parent || '');
  }

  function jumpToCategory(cat: string) {
    setViewMode('flat');
    selectCategory(cat);
  }

  function jumpToFolder(folderPath: string) {
    setViewMode('folder');
    openFolder(folderPath);
  }

  function setSearch(q: string) {
    searchQuery = q;
    updateHash(true);
  }

  function clearSearch() {
    searchQuery = '';
    updateHash(true);
  }

  async function loadData(forceReload = false) {
    try {
      if (forceReload) isRescanning = true;
      else isLoading = true;

      const url = forceReload ? '/api/sounds?reload=true' : '/api/sounds';
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);

      const data: SoundsResponse = await res.json();
      sounds = data.sounds || [];
      folders = data.folders || {};
      categories = ['All', ...(data.categories || [])];
      appVersion = data.version || '';

      if (data.config) {
        if (data.config.app_title) {
          appTitle = data.config.app_title;
          document.title = appTitle;
        }
        if (data.config.audio_cache_size) {
          audio.setCacheSize(data.config.audio_cache_size);
        }
      }

      if (forceReload) {
        showToast('Library rescanned successfully');
      }
    } catch (err) {
      console.error('Failed to load sounds:', err);
      showToast('Error loading audio catalog');
    } finally {
      isLoading = false;
      isRescanning = false;
    }
  }

  // Filtered queries
  const searchNormalized = $derived(searchQuery.trim().toLowerCase());

  const searchSounds = $derived.by<Sound[]>(() => {
    if (!searchNormalized) return sounds;
    return sounds.filter((s) => {
      return (
        s.title.toLowerCase().includes(searchNormalized) ||
        s.filename.toLowerCase().includes(searchNormalized) ||
        s.category.toLowerCase().includes(searchNormalized) ||
        s.folder.toLowerCase().includes(searchNormalized)
      );
    });
  });

  const categoryCounts = $derived.by<Record<string, number>>(() => {
    const counts: Record<string, number> = { All: sounds.length };
    for (const s of sounds) {
      const cat = s.category || 'General';
      counts[cat] = (counts[cat] || 0) + 1;
    }
    return counts;
  });

  // Flat View sounds
  const flatSounds = $derived.by<Sound[]>(() => {
    const base = searchNormalized ? searchSounds : sounds;
    if (activeCategory === 'All') return base;
    return base.filter((s) => s.category === activeCategory);
  });

  // Folder View subfolders and direct sounds
  const currentFolderObj = $derived<FolderInfo | undefined>(folders[currentFolder]);

  const displayedSubfolders = $derived.by<FolderInfo[]>(() => {
    if (searchNormalized) {
      // Find matching folders across the entire tree
      const matched: FolderInfo[] = [];
      for (const f of Object.values(folders)) {
        if (
          f.name.toLowerCase().includes(searchNormalized) ||
          f.path.toLowerCase().includes(searchNormalized)
        ) {
          matched.push(f);
        }
      }
      return matched;
    }

    const subPaths = currentFolderObj?.subfolders || [];
    return subPaths.map((p) => folders[p]).filter(Boolean);
  });

  const displayedFolderSounds = $derived.by<Sound[]>(() => {
    if (searchNormalized) {
      return searchSounds;
    }
    const soundIds = currentFolderObj?.sound_ids || [];
    const soundMap = new Map(sounds.map((s) => [s.id, s]));
    return soundIds.map((id) => soundMap.get(id)).filter((s): s is Sound => Boolean(s));
  });

  const hasNoSearchResults = $derived(
    Boolean(searchNormalized) &&
      (viewMode === 'flat'
        ? flatSounds.length === 0
        : displayedSubfolders.length === 0 && displayedFolderSounds.length === 0)
  );

  onMount(() => {
    // Restore persisted view mode
    const savedView = localStorage.getItem('soundboard_view_mode') as ViewMode | null;
    if (savedView === 'flat' || savedView === 'folder') {
      viewMode = savedView;
    }

    // Sync from URL hash
    syncFromHash(window.location.hash);
    const onNavChange = () => syncFromHash(window.location.hash);
    window.addEventListener('hashchange', onNavChange);
    window.addEventListener('popstate', onNavChange);

    // Load initial sounds and config
    loadData();

    // Global Hotkeys: Esc -> Stop All, / -> Search
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        audio.stopAll();
      } else if (e.key === '/' && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault();
        headerComponent?.focusSearch();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('hashchange', onNavChange);
      window.removeEventListener('popstate', onNavChange);
    };
  });
</script>

<div class="min-h-full flex flex-col">
  <!-- Header Bar -->
  <Header
    bind:this={headerComponent}
    {appTitle}
    {viewMode}
    {searchQuery}
    {categories}
    {activeCategory}
    {isRescanning}
    totalSoundCount={sounds.length}
    {categoryCounts}
    {currentFolder}
    {breadcrumbs}
    onSelectCategory={selectCategory}
    onToggleView={setViewMode}
    onSearchChange={setSearch}
    onClearSearch={clearSearch}
    onRescan={() => loadData(true)}
    onOpenFolder={openFolder}
    onGoToParent={goToParentFolder}
  />

  <!-- Main Content Area -->
  <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
    {#if isLoading}
      <!-- Loading Skeleton Shell -->
      <div class="space-y-6">
        <div class="flex items-center gap-2 text-indigo-400 text-sm font-semibold animate-pulse">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span>Scanning audio library...</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {#each Array(12) as _, i (i)}
            <div class="aspect-[4/3] rounded-2xl bg-slate-900/60 border border-slate-800/60 animate-pulse"></div>
          {/each}
        </div>
      </div>
    {:else if hasNoSearchResults}
      <!-- Unified Empty Search State -->
      <EmptySearch
        {searchQuery}
        {viewMode}
        {currentFolder}
        onClearSearch={clearSearch}
        onReturnHome={() => openFolder('')}
      />
    {:else if viewMode === 'flat'}
      <!-- Flat / Category View -->
      <FlatView
        sounds={flatSounds}
        {activeCategory}
        {searchQuery}
        onJumpCategory={jumpToCategory}
        onJumpFolder={jumpToFolder}
      />
    {:else if viewMode === 'folder'}
      <!-- Hierarchical Folder View -->
      <FolderView
        {currentFolder}
        {currentFolderObj}
        subfolders={displayedSubfolders}
        sounds={displayedFolderSounds}
        {searchQuery}
        searchSoundCount={searchSounds.length}
        onOpenFolder={openFolder}
        onJumpCategory={jumpToCategory}
        onJumpFolder={jumpToFolder}
        onGoToParent={goToParentFolder}
      />
    {/if}
  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800/60 py-4 text-center text-xs text-slate-500">
    <p class="flex items-center justify-center flex-wrap gap-x-2 gap-y-1">
      <span class="inline-flex items-center gap-1.5">
        <span>{appTitle}</span>
        {#if appVersion}
          <a
            href="https://github.com/MisterX2000/3Sound/releases/tag/v{appVersion}"
            target="_blank"
            rel="noopener noreferrer"
            title="View release on GitHub"
            class="inline-flex items-center px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700/80 font-mono text-[10px] transition-colors"
          >
            v{appVersion}
          </a>
        {/if}
      </span>
      <span>&bull;</span>
      <span>Click card to play</span>
      <span>&bull;</span>
      <span>Click <kbd class="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-emerald-400 font-mono text-[10px]">LOOP</kbd> to loop</span>
      <span>&bull;</span>
      <span>Press <kbd class="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono text-[10px]">Esc</kbd> to stop all</span>
    </p>
  </footer>

  <!-- Toast Notification -->
  <Toast message={toastMessage} />
</div>
