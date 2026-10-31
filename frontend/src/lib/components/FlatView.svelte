<script lang="ts">
  import { onMount } from 'svelte';
  import type { Sound } from '../../types';
  import SoundCard from './SoundCard.svelte';
  import { Folder, Loader2 } from '@lucide/svelte';

  interface Props {
    sounds: Sound[];
    activeCategory: string;
    searchQuery: string;
    onJumpCategory: (category: string) => void;
    onJumpFolder: (folder: string) => void;
  }

  const { sounds, activeCategory, searchQuery, onJumpCategory, onJumpFolder }: Props = $props();

  let renderLimit = $state(80);
  let sentinelEl = $state<HTMLDivElement | null>(null);

  interface CategoryGroup {
    name: string;
    sounds: Sound[];
  }

  const displayedSounds = $derived(sounds.slice(0, renderLimit));
  const hasMore = $derived(sounds.length > renderLimit);

  const categoryGroups = $derived.by<CategoryGroup[]>(() => {
    if (activeCategory !== 'All' && !searchQuery) {
      return [{ name: activeCategory, sounds: displayedSounds }];
    }

    const groupMap = new Map<string, Sound[]>();
    for (const s of displayedSounds) {
      const cat = s.category || 'General';
      let list = groupMap.get(cat);
      if (!list) {
        list = [];
        groupMap.set(cat, list);
      }
      list.push(s);
    }

    return Array.from(groupMap.entries()).map(([name, groupSounds]) => ({
      name,
      sounds: groupSounds,
    }));
  });

  onMount(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting && hasMore) {
        renderLimit += 60;
      }
    }, { rootMargin: '400px' });

    if (sentinelEl) observer.observe(sentinelEl);

    return () => {
      observer.disconnect();
    };
  });
</script>

<div class="space-y-8">
  {#each categoryGroups as group (group.name)}
    <section class="space-y-3">
      <!-- Category Subtitle Header -->
      <div class="flex items-center gap-2 text-sm font-semibold text-slate-300 border-b border-slate-800/80 pb-2">
        <Folder class="w-4 h-4 text-indigo-400" />
        <span>{group.name}</span>
        <span class="text-xs text-slate-500 font-normal">({group.sounds.length})</span>
      </div>

      <!-- Responsive Sound Cards Grid -->
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {#each group.sounds as sound (sound.id)}
          <SoundCard
            {sound}
            viewMode="flat"
            {onJumpCategory}
            {onJumpFolder}
          />
        {/each}
      </div>
    </section>
  {/each}

  <!-- Infinite Scroll Sentinel -->
  <div bind:this={sentinelEl} id="infinite-scroll-sentinel" class="py-6 flex flex-col items-center justify-center text-slate-500">
    {#if hasMore}
      <div class="flex items-center gap-2 text-xs">
        <Loader2 class="animate-spin h-4 w-4 text-indigo-500" />
        <span>Loading more sounds...</span>
      </div>
    {:else if searchQuery && sounds.length > 80}
      <div class="text-xs text-slate-600">
        All {sounds.length} matching sounds loaded
      </div>
    {/if}
  </div>
</div>
