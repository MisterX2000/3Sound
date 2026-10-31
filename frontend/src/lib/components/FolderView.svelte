<script lang="ts">
  import type { FolderInfo, Sound } from '../../types';
  import FolderCard from './FolderCard.svelte';
  import SoundCard from './SoundCard.svelte';
  import { Folder, Music, ArrowLeft, FolderOpen } from '@lucide/svelte';

  interface Props {
    currentFolder: string;
    currentFolderObj?: FolderInfo;
    subfolders: FolderInfo[];
    sounds: Sound[];
    searchQuery: string;
    searchSoundCount: number;
    onOpenFolder: (path: string) => void;
    onJumpCategory: (category: string) => void;
    onJumpFolder: (folder: string) => void;
    onGoToParent: () => void;
  }

  const {
    currentFolder,
    currentFolderObj,
    subfolders,
    sounds,
    searchQuery,
    searchSoundCount,
    onOpenFolder,
    onJumpCategory,
    onJumpFolder,
    onGoToParent,
  }: Props = $props();

  const folderName = $derived(
    searchQuery
      ? `Search Results: "${searchQuery}"`
      : currentFolderObj?.name || 'All Sounds'
  );

  const folderStats = $derived(
    `${subfolders.length} ${subfolders.length === 1 ? 'folder' : 'folders'} • ${searchQuery ? searchSoundCount : sounds.length} ${(searchQuery ? searchSoundCount : sounds.length) === 1 ? 'sound' : 'sounds'}`
  );
</script>

<div class="space-y-8">
  <!-- Current Folder Header -->
  <div class="flex items-center justify-between pb-3 border-b border-slate-800/80">
    <div class="flex items-center gap-3">
      <div class="h-9 w-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shadow-sm">
        <FolderOpen class="w-5 h-5" />
      </div>
      <div>
        <h2 class="text-base font-bold text-white leading-tight">{folderName}</h2>
        <p class="text-xs text-slate-400">{folderStats}</p>
      </div>
    </div>

    {#if currentFolder && !searchQuery}
      <button
        type="button"
        onclick={onGoToParent}
        class="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1.5 transition shadow-sm cursor-pointer"
        title="Go to parent directory"
      >
        <ArrowLeft class="w-3.5 h-3.5" />
        <span class="hidden sm:inline">Up one level</span>
      </button>
    {/if}
  </div>

  <!-- Subfolders Section -->
  {#if subfolders.length > 0}
    <div class="space-y-3">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
        <Folder class="w-3.5 h-3.5 text-indigo-400" />
        <span>{searchQuery ? 'Matching Folders' : 'Folders'}</span>
        <span class="text-[11px] font-normal text-slate-500">({subfolders.length})</span>
      </h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {#each subfolders as folder (folder.path)}
          <FolderCard
            {folder}
            {searchQuery}
            {onOpenFolder}
          />
        {/each}
      </div>
    </div>
  {/if}

  <!-- Sounds in Folder Section -->
  {#if sounds.length > 0}
    <div class="space-y-3">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
        <Music class="w-3.5 h-3.5 text-indigo-400" />
        <span>{searchQuery ? 'Matching Sounds' : 'Sounds'}</span>
        <span class="text-[11px] font-normal text-slate-500">({searchQuery ? searchSoundCount : sounds.length})</span>
      </h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {#each sounds as sound (sound.id)}
          <SoundCard
            {sound}
            viewMode="folder"
            {onJumpCategory}
            {onJumpFolder}
          />
        {/each}
      </div>
    </div>
  {/if}

  <!-- Empty Folder State (when not searching) -->
  {#if !searchQuery && subfolders.length === 0 && sounds.length === 0}
    <div class="flex flex-col items-center justify-center py-16 text-center">
      <div class="h-12 w-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mb-3 shadow-inner">
        <Folder class="w-6 h-6 text-slate-500" />
      </div>
      <p class="text-sm font-medium text-slate-300">This folder is empty</p>
      <p class="text-xs text-slate-500 mt-0.5 mb-4">No audio files or subfolders found here</p>
      {#if currentFolder}
        <button
          type="button"
          onclick={onGoToParent}
          class="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-xs text-slate-300 flex items-center gap-1.5 transition shadow-sm cursor-pointer"
        >
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Go to parent folder</span>
        </button>
      {/if}
    </div>
  {/if}
</div>
