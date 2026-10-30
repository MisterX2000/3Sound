<script lang="ts">
  import type { BreadcrumbItem, ViewMode } from '../../types';
  import { audio } from '../audio.svelte';
  import {
    Search,
    X,
    Volume2,
    VolumeX,
    Square,
    RotateCw,
    Folder,
    LayoutGrid,
    Home,
    ChevronRight,
    ArrowLeft
  } from '@lucide/svelte';

  interface Props {
    appTitle: string;
    viewMode: ViewMode;
    searchQuery: string;
    categories: string[];
    activeCategory: string;
    isRescanning: boolean;
    totalSoundCount: number;
    categoryCounts: Record<string, number>;
    currentFolder: string;
    breadcrumbs: BreadcrumbItem[];
    onSelectCategory: (cat: string) => void;
    onToggleView: (mode: ViewMode) => void;
    onSearchChange: (q: string) => void;
    onClearSearch: () => void;
    onRescan: () => void;
    onOpenFolder: (path: string) => void;
    onGoToParent: () => void;
  }

  let {
    appTitle,
    viewMode,
    searchQuery,
    categories,
    activeCategory,
    isRescanning,
    totalSoundCount,
    categoryCounts,
    currentFolder,
    breadcrumbs,
    onSelectCategory,
    onToggleView,
    onSearchChange,
    onClearSearch,
    onRescan,
    onOpenFolder,
    onGoToParent,
  }: Props = $props();

  let searchInputEl = $state<HTMLInputElement | null>(null);

  export function focusSearch() {
    searchInputEl?.focus();
    searchInputEl?.select();
  }

  const volumePercent = $derived(
    audio.isMuted ? '0%' : `${Math.round(audio.masterVolume * 100)}%`
  );
</script>

<header class="sticky top-0 z-40 bg-slate-950/85 backdrop-blur-xl border-b border-slate-800/80 px-4 py-3 sm:px-6">
  <div class="max-w-7xl mx-auto flex flex-col gap-2.5">
    
    <!-- Top Row: Logo/Title, Centered Search Bar, Controls -->
    <div class="flex flex-col md:flex-row items-center justify-between gap-3">
      
      <!-- Left: App Brand & Subtitle -->
      <div class="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white shrink-0">
            <Volume2 class="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 class="text-lg font-bold tracking-tight text-white flex items-center gap-2 flex-wrap">
              <span>{appTitle}</span>
              <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-indigo-300 border border-slate-700 whitespace-nowrap">
                {totalSoundCount} Sounds
              </span>
            </h1>
            <p class="text-xs text-slate-400 hidden sm:block whitespace-nowrap">Click any button to play sound</p>
          </div>
        </div>

        <!-- Mobile Stop All button (Always visible to prevent DOM shifts) -->
        <button
          type="button"
          onclick={() => audio.stopAll()}
          disabled={audio.playingIds.length === 0}
          title={audio.playingIds.length > 0 ? "Stop all currently playing sounds (Esc)" : "No sounds currently playing"}
          class="md:hidden flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-xs font-medium shrink-0 transition {audio.playingIds.length > 0 ? 'bg-rose-500/20 text-rose-400 border-rose-500/30 hover:bg-rose-500/30 cursor-pointer' : 'bg-slate-900/50 text-slate-500 border-slate-800/60 opacity-40 cursor-not-allowed'}"
        >
          <Square class="w-3.5 h-3.5 {audio.playingIds.length > 0 ? 'fill-current' : 'opacity-60'}" />
          <span>Stop All</span>
        </button>
      </div>

      <!-- Center: Search Bar -->
      <div class="relative w-full md:max-w-md">
        <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
          <Search class="h-4 w-4" />
        </div>
        <input
          bind:this={searchInputEl}
          id="soundboard-search"
          name="q"
          type="search"
          placeholder="Search sounds or categories... (Press / to focus)"
          value={searchQuery}
          oninput={(e) => onSearchChange((e.target as HTMLInputElement).value)}
          class="w-full pl-10 pr-9 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
          aria-label="Search sounds or categories"
        />
        {#if searchQuery}
          <button
            type="button"
            onclick={onClearSearch}
            class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 cursor-pointer"
            title="Clear search"
          >
            <X class="h-4 w-4" />
          </button>
        {/if}
      </div>

      <!-- Right: Controls Toolbar -->
      <div class="flex items-center gap-2 sm:gap-2.5 w-full md:w-auto justify-end flex-wrap sm:flex-nowrap">
        
        <!-- View Mode Switch: Flat vs Folders -->
        <div class="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs shadow-inner">
          <button
            type="button"
            onclick={() => onToggleView('flat')}
            title="Flat View (All categories)"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition font-medium cursor-pointer"
            class:bg-indigo-600={viewMode === 'flat'}
            class:text-white={viewMode === 'flat'}
            class:shadow-sm={viewMode === 'flat'}
            class:text-slate-400={viewMode !== 'flat'}
            class:hover:text-slate-200={viewMode !== 'flat'}
          >
            <LayoutGrid class="w-3.5 h-3.5" />
            <span>Flat</span>
          </button>
          <button
            type="button"
            onclick={() => onToggleView('folder')}
            title="Folder View (Browse directory hierarchy)"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition font-medium cursor-pointer"
            class:bg-indigo-600={viewMode === 'folder'}
            class:text-white={viewMode === 'folder'}
            class:shadow-sm={viewMode === 'folder'}
            class:text-slate-400={viewMode !== 'folder'}
            class:hover:text-slate-200={viewMode !== 'folder'}
          >
            <Folder class="w-3.5 h-3.5" />
            <span>Folders</span>
          </button>
        </div>

        <!-- Master Volume Slider with Percentage Display -->
        <div class="flex items-center gap-2 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl shadow-inner">
          <button
            type="button"
            onclick={() => audio.toggleMute()}
            title={audio.isMuted ? 'Unmute master audio' : 'Mute master audio'}
            class="text-slate-400 hover:text-slate-200 transition cursor-pointer"
          >
            {#if audio.isMuted || audio.masterVolume === 0}
              <VolumeX class="w-4 h-4 text-rose-400" />
            {:else}
              <Volume2 class="w-4 h-4 text-indigo-400" />
            {/if}
          </button>
          <input
            id="master-volume"
            name="volume"
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={audio.masterVolume}
            oninput={(e) => audio.setVolume(parseFloat((e.target as HTMLInputElement).value))}
            class="w-16 sm:w-20 accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
            title="Master volume ({volumePercent})"
            aria-label="Master volume control"
          />
          <span class="text-[11px] text-slate-400 font-mono w-7 text-right select-none">{volumePercent}</span>
        </div>

        <!-- Desktop Stop All Button (Always visible to prevent DOM shifts) -->
        <button
          type="button"
          onclick={() => audio.stopAll()}
          disabled={audio.playingIds.length === 0}
          title={audio.playingIds.length > 0 ? "Stop all currently playing sounds (Esc)" : "No sounds currently playing"}
          class="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-xl border transition text-xs font-medium shadow-sm whitespace-nowrap shrink-0 {audio.playingIds.length > 0 ? 'bg-rose-500/20 text-rose-400 border-rose-500/30 hover:bg-rose-500/30 cursor-pointer' : 'bg-slate-900/50 text-slate-500 border-slate-800/60 opacity-40 cursor-not-allowed'}"
        >
          <Square class="w-3.5 h-3.5 {audio.playingIds.length > 0 ? 'fill-current' : 'opacity-60'}" />
          <span>Stop All</span>
        </button>

        <!-- Rescan Button -->
        <button
          type="button"
          onclick={onRescan}
          disabled={isRescanning}
          title="Rescan sounds directory from filesystem"
          class="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition cursor-pointer shadow-sm disabled:opacity-50"
        >
          <RotateCw class="h-4 w-4 {isRescanning ? 'animate-spin text-indigo-400' : ''}" />
        </button>

      </div>
    </div>

    <!-- Row 2: Navigation / Filter Subheader Bar -->
    <div class="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-3 overflow-hidden min-h-[40px]">
      
      <!-- Flat View: Category Pills Carousel -->
      {#if viewMode === 'flat'}
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-xs flex-1">
          <div class="flex items-center gap-1.5">
            {#each categories as cat (cat)}
              {@const count = categoryCounts[cat] || 0}
              <button
                type="button"
                onclick={() => onSelectCategory(cat)}
                class="px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition flex items-center gap-1.5 cursor-pointer"
                class:bg-indigo-600={activeCategory === cat}
                class:text-white={activeCategory === cat}
                class:shadow-md={activeCategory === cat}
                class:shadow-indigo-600={activeCategory === cat}
                class:bg-slate-900={activeCategory !== cat}
                class:text-slate-300={activeCategory !== cat}
                class:hover:bg-slate-800={activeCategory !== cat}
                class:hover:text-white={activeCategory !== cat}
                class:border={activeCategory !== cat}
                class:border-slate-800={activeCategory !== cat}
              >
                <span>{cat}</span>
                <span
                  class="text-[10px] px-1.5 py-0.2 rounded-full"
                  class:bg-indigo-700={activeCategory === cat}
                  class:text-indigo-100={activeCategory === cat}
                  class:bg-slate-800={activeCategory !== cat}
                  class:text-slate-400={activeCategory !== cat}
                >
                  {count}
                </span>
              </button>
            {/each}
          </div>
        </div>
      {:else}
        <!-- Folder View: Interactive Breadcrumbs Bar -->
        <div class="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs flex-1">
          {#if currentFolder}
            <button
              type="button"
              onclick={onGoToParent}
              title="Go up to parent folder"
              class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 hover:border-slate-700 transition font-medium shrink-0 shadow-sm cursor-pointer"
            >
              <ArrowLeft class="w-3.5 h-3.5" />
              <span>Up</span>
            </button>
          {/if}

          <div class="flex items-center gap-1.5 text-xs text-slate-400 overflow-x-auto scrollbar-none">
            <!-- Home Breadcrumb -->
            <button
              type="button"
              onclick={() => onOpenFolder('')}
              class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition shrink-0 cursor-pointer"
              class:text-white={currentFolder === ''}
              class:font-semibold={currentFolder === ''}
              class:bg-slate-900={currentFolder === ''}
              class:border={currentFolder === ''}
              class:border-slate-700={currentFolder === ''}
              class:shadow-sm={currentFolder === ''}
              class:text-slate-400={currentFolder !== ''}
              class:hover:text-slate-200={currentFolder !== ''}
            >
              <Home class="w-3.5 h-3.5 text-indigo-400" />
              <span>Home</span>
            </button>

            <!-- Nested Path Breadcrumbs -->
            {#each breadcrumbs as crumb (crumb.path)}
              <div class="flex items-center gap-1.5 shrink-0">
                <ChevronRight class="w-3 h-3 text-slate-600 select-none" />
                <button
                  type="button"
                  onclick={() => !crumb.isLast && onOpenFolder(crumb.path)}
                  class="px-2.5 py-1 rounded-lg transition shrink-0"
                  class:text-white={crumb.isLast}
                  class:font-semibold={crumb.isLast}
                  class:bg-slate-900={crumb.isLast}
                  class:border={crumb.isLast}
                  class:border-slate-700={crumb.isLast}
                  class:shadow-sm={crumb.isLast}
                  class:cursor-default={crumb.isLast}
                  class:text-slate-400={!crumb.isLast}
                  class:hover:text-slate-200={!crumb.isLast}
                  class:cursor-pointer={!crumb.isLast}
                >
                  <span>{crumb.name}</span>
                </button>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Overlap Switch Toggle -->
      <label class="flex items-center gap-2 cursor-pointer text-xs text-slate-400 select-none whitespace-nowrap shrink-0">
        <input
          type="checkbox"
          checked={audio.allowOverlap}
          onchange={() => audio.toggleOverlap()}
          class="sr-only peer"
        />
        <div class="w-7 h-4 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-600 relative"></div>
        <span class="text-slate-300 font-medium">Overlap</span>
      </label>

    </div>

  </div>
</header>
