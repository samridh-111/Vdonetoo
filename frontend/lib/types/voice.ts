export interface Voice {
  id: string;
  name: string;
  preset_key: string;
  language_code: string | null;
  similarity: number;
  stability: number;
  style: number;
  speed: number;
  sample_audio_url: string | null;
  is_active: boolean;
}

export interface VoicePreviewResponse {
  voice_id: string;
  audio_base64: string;
  content_type: string;
}
