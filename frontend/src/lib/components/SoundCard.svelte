<script lang="ts">
  import { onMount } from 'svelte';
  import type { Sound, ViewMode } from '../../types';
  import { audio } from '../audio.svelte';
  import { Play, Square, Repeat, Clock, Folder, ChevronRight, Music } from '@lucide/svelte';

  interface Props {
    sound: Sound;
    viewMode: ViewMode;
    onJumpCategory?: (category: string) => void;
    onJumpFolder?: (folder: string) => void;
  }

  const { sound, viewMode, onJumpCategory, onJumpFolder }: Props = $props();

  let progressBarEl = $state<HTMLDivElement | null>(null);
  let fadeTimeout: number | null = null;
  let isEnding = $state(false);
  let endingTimeout: number | null = null;

  const isPlaying = $derived(audio.isPlaying(sound.id));
  const isLooping = $derived(audio.isLooping(sound.id));

  onMount(() => {
    // Listen for progress updates directed to this sound or global stop-all
    const handleProgress = (e: CustomEvent<{ soundId: string; duration: number; type: string }>) => {
      if (!progressBarEl) return;
      if (e.detail.soundId !== sound.id && e.detail.soundId !== 'all') return;

      if (fadeTimeout) {
        clearTimeout(fadeTimeout);
        fadeTimeout = null;
      }

      if (e.detail.type === 'play' || e.detail.type === 'loop') {
        isEnding = false;
        if (endingTimeout) {
          clearTimeout(endingTimeout);
          endingTimeout = null;
        }
        progressBarEl.style.transition = 'none';
        progressBarEl.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
        progressBarEl.style.transform = 'scaleX(0)';
        progressBarEl.style.opacity = '';
        void progressBarEl.offsetWidth; // Force reflow to restart CSS animation cleanly
        progressBarEl.style.transition = '';
        progressBarEl.style.setProperty('--sound-duration', `${e.detail.duration}s`);
        progressBarEl.classList.add('is-animating');
        if (e.detail.type === 'loop' || isLooping) {
          progressBarEl.classList.add('is-looping');
        }
      } else if (e.detail.type === 'stop') {
        isEnding = true;
        if (endingTimeout) clearTimeout(endingTimeout);
        endingTimeout = window.setTimeout(() => {
          isEnding = false;
          endingTimeout = null;
        }, 270);

        progressBarEl.classList.add('is-paused', 'is-fading');
        fadeTimeout = window.setTimeout(() => {
          if (progressBarEl) {
            progressBarEl.style.transition = 'none';
            progressBarEl.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
            progressBarEl.style.transform = 'scaleX(0)';
            progressBarEl.style.opacity = '';
            void progressBarEl.offsetWidth;
            progressBarEl.style.transition = '';
          }
          fadeTimeout = null;
        }, 270);
      } else if (e.detail.type === 'end') {
        isEnding = true;
        if (endingTimeout) clearTimeout(endingTimeout);
        endingTimeout = window.setTimeout(() => {
          isEnding = false;
          endingTimeout = null;
        }, 270);

        fadeTimeout = window.setTimeout(() => {
          if (progressBarEl) {
            progressBarEl.classList.add('is-fading');
            fadeTimeout = window.setTimeout(() => {
              if (progressBarEl) {
                progressBarEl.style.transition = 'none';
                progressBarEl.classList.remove('is-animating', 'is-looping', 'is-paused', 'is-fading');
                progressBarEl.style.transform = 'scaleX(0)';
                progressBarEl.style.opacity = '';
                void progressBarEl.offsetWidth;
                progressBarEl.style.transition = '';
              }
              fadeTimeout = null;
            }, 250);
          }
        }, 150);
      }
    };

    window.addEventListener('sound-progress', handleProgress as EventListener);
    return () => {
      if (fadeTimeout) clearTimeout(fadeTimeout);
      if (endingTimeout) clearTimeout(endingTimeout);
      window.removeEventListener('sound-progress', handleProgress as EventListener);
    };
  });

  function handleCardClick(e: MouseEvent | KeyboardEvent) {
    // If clicking a button or anchor inside, let it handle
    const target = e.target as HTMLElement;
    if (target.closest('button')) return;
    audio.play(sound);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleCardClick(e);
    }
  }
</script>

<div
  role="button"
  tabindex="0"
  onclick={handleCardClick}
  onkeydown={handleKeyDown}
  class="group relative flex flex-col text-left rounded-2xl bg-slate-900 border border-slate-800/90 shadow-md transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0 overflow-hidden cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
  class:ring-2={isPlaying}
  class:ring-emerald-500={isPlaying && isLooping}
  class:border-emerald-500={isPlaying && isLooping}
  class:ring-indigo-500={isPlaying && !isLooping}
  class:border-indigo-500={isPlaying && !isLooping}
  class:bg-slate-800={isPlaying}
>
  <!-- Artwork Container -->
  <div class="relative w-full aspect-[4/3] bg-slate-950 overflow-hidden flex items-center justify-center">
    {#if sound.image_url}
      <img
        src={sound.image_url}
        alt={sound.title}
        loading="lazy"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />
    {:else}
      <div class="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 to-slate-950 text-slate-600 group-hover:text-indigo-400 group-hover:from-slate-900 group-hover:to-indigo-950/20 transition-all">
        <Music class="w-10 h-10 transform group-hover:scale-110 transition-transform" />
      </div>
    {/if}

    <!-- Gradient Overlay -->
    <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent pointer-events-none"></div>

    <!-- Top Left Badges: Format & Loop Button -->
    <div class="absolute top-2 left-2 flex items-center gap-1.5 z-20">
      <span class="px-1.5 py-0.5 rounded bg-slate-950/80 backdrop-blur-md border border-slate-700/60 text-[10px] font-mono uppercase text-slate-300 pointer-events-none select-none">
        {sound.format}
      </span>
      <button
        type="button"
        onclick={(e) => {
          e.stopPropagation();
          audio.toggleLoop(sound);
        }}
        class="px-1.5 py-0.5 rounded backdrop-blur-md border text-[10px] font-mono flex items-center gap-1 transition-all duration-200 cursor-pointer"
        class:bg-emerald-500={isLooping}
        class:text-white={isLooping}
        class:border-emerald-400={isLooping}
        class:shadow-md={isLooping}
        class:shadow-emerald-500={isLooping}
        class:bg-slate-950={!isLooping}
        class:border-slate-700={!isLooping}
        class:text-slate-400={!isLooping}
        class:hover:text-slate-200={!isLooping}
        title={isLooping ? 'Looping enabled (Click to toggle)' : 'Enable loop'}
      >
        <Repeat class="w-3 h-3 text-current" />
        <span class="text-[9px] font-bold tracking-wider">{isLooping ? 'LOOP' : '1x'}</span>
      </button>
    </div>

    <!-- Duration Badge (Top Right) -->
    <div class="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-slate-950/80 backdrop-blur-md border border-slate-700/60 text-[10px] font-mono text-slate-200 flex items-center gap-1 z-10 pointer-events-none">
      <Clock class="w-2.5 h-2.5 text-slate-400" />
      <span>{sound.duration_formatted || '0:00'}</span>
    </div>

    <!-- Play/Stop Overlay Icon -->
    <div
      class="absolute inset-0 flex items-center justify-center transition-opacity duration-200 bg-black/30 backdrop-blur-[1px] pointer-events-none"
      class:opacity-100={isPlaying}
      class:opacity-0={!isPlaying}
      class:group-hover:opacity-100={!isPlaying && !isEnding}
    >
      {#if isPlaying || isEnding}
        <button
          type="button"
          onclick={(e) => {
            e.stopPropagation();
            audio.stop(sound.id);
          }}
          title="Stop playback"
          class="w-10 h-10 rounded-full text-white flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 hover:scale-105 active:scale-95 transition-all pointer-events-auto cursor-pointer"
          class:bg-emerald-600={isLooping}
          class:hover:bg-emerald-500={isLooping}
          class:bg-rose-600={!isLooping}
          class:hover:bg-rose-500={!isLooping}
        >
          <Square class="w-4 h-4 fill-current" />
        </button>
      {:else}
        <div class="w-10 h-10 rounded-full bg-indigo-600 shadow-indigo-600/50 text-white flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 transition-transform pointer-events-none">
          <Play class="w-4 h-4 fill-current ml-0.5" />
        </div>
      {/if}
    </div>
  </div>

  <!-- Info Card Body -->
  <div class="p-3 w-full flex-1 flex flex-col justify-between">
    <div>
      <h4 title={sound.title} class="font-semibold text-sm text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1">
        {sound.title}
      </h4>

      {#if viewMode === 'flat'}
        <button
          type="button"
          onclick={(e) => {
            e.stopPropagation();
            onJumpCategory?.(sound.category);
          }}
          class="text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline inline-flex items-center gap-1 truncate mt-0.5 cursor-pointer"
          title="Jump to this category"
        >
          <span>{sound.category}</span>
          <ChevronRight class="w-2.5 h-2.5 opacity-70" />
        </button>
      {:else}
        <button
          type="button"
          onclick={(e) => {
            e.stopPropagation();
            onJumpFolder?.(sound.folder);
          }}
          class="text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline inline-flex items-center gap-1 truncate mt-0.5 cursor-pointer"
          title="Open this folder in soundboard"
        >
          <Folder class="w-2.5 h-2.5 opacity-70 shrink-0" />
          <span>{sound.folder || 'Home'}</span>
          <ChevronRight class="w-2.5 h-2.5 opacity-70 shrink-0" />
        </button>
      {/if}
    </div>
  </div>

  <!-- GPU-Accelerated Audio Progress Bar -->
  <div class="progress-bar-container w-full h-1 bg-slate-800 overflow-hidden relative">
    <div
      bind:this={progressBarEl}
      data-progress-id={sound.id}
      class="progress-bar w-full h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 pointer-events-none"
    ></div>
  </div>
</div>
