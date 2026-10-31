export interface Sound {
  id: string;
  title: string;
  filename: string;
  folder: string;
  category: string;
  format: string;
  duration: number;
  duration_formatted?: string;
  sound_url: string;
  image_url: string | null;
  has_embedded_cover?: boolean;
}

export interface FolderInfo {
  path: string;
  name: string;
  parent: string | null;
  image_url: string | null;
  subfolders: string[];
  sound_ids: string[];
  sound_count: number;
  total_sound_count: number;
}

export interface ClientConfig {
  app_title: string;
  default_view_mode: ViewMode;
  default_volume: number;
  default_allow_overlap: boolean;
  default_muted: boolean;
  audio_cache_size: number;
}

export interface SoundsResponse {
  sounds: Sound[];
  folders: Record<string, FolderInfo>;
  categories: string[];
  version: string;
  config: ClientConfig;
}

export interface BreadcrumbItem {
  name: string;
  path: string;
  isLast: boolean;
}

export type ViewMode = 'flat' | 'folder';
