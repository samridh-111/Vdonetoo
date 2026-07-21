"use client";

import { useRef, useState } from "react";
import { useVoicePreview } from "@/lib/hooks/useVoicePreview";
import { useVoices } from "@/lib/hooks/useVoices";
import type { Voice } from "@/lib/types/voice";

interface VoiceSelectionListProps {
  selectedVoiceId: string | null;
  onSelect: (voice: Voice) => void;
}

export function VoiceSelectionList({ selectedVoiceId, onSelect }: VoiceSelectionListProps) {
  const { data: voices = [] } = useVoices();
  const preview = useVoicePreview();
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [showAll, setShowAll] = useState(false);

  const visibleVoices = showAll ? voices : voices.slice(0, 2);

  async function togglePlay(event: React.MouseEvent, voice: Voice) {
    event.stopPropagation();

    if (playingId === voice.id) {
      audioRef.current?.pause();
      setPlayingId(null);
      return;
    }

    const result = await preview.mutateAsync(voice.id);
    const audio = new Audio(`data:${result.content_type};base64,${result.audio_base64}`);
    audioRef.current?.pause();
    audioRef.current = audio;
    audio.onended = () => setPlayingId(null);
    setPlayingId(voice.id);
    await audio.play();
  }

  return (
    <section className="space-y-md">
      <div className="flex items-center justify-between">
        <h3 className="text-title-md font-medium text-on-surface">Voice Selection</h3>
        <button
          type="button"
          className="text-xs text-on-surface-variant/50 hover:text-primary transition-colors"
          onClick={() => setShowAll((prev) => !prev)}
        >
          {showAll ? "Show less" : "See all"}
        </button>
      </div>
      <div className="space-y-2">
        {visibleVoices.map((voice) => {
          const isSelected = voice.id === selectedVoiceId;
          const isPlaying = playingId === voice.id;
          return (
            <div
              key={voice.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(voice)}
              className={`flex items-center gap-3 p-2 rounded-lg border cursor-pointer transition-colors group ${
                isSelected ? "bg-white/[0.03] minimal-divider" : "border-transparent hover:bg-white/[0.02]"
              }`}
            >
              <div className="w-8 h-8 rounded bg-surface-container-high flex items-center justify-center text-on-surface-variant/60 text-xs font-bold shrink-0">
                {voice.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <h4
                  className={`text-body-sm font-medium truncate ${
                    isSelected ? "text-on-surface" : "text-on-surface-variant/60"
                  }`}
                >
                  {voice.name}
                </h4>
                <p className={`text-[11px] ${isSelected ? "text-on-surface-variant/50" : "text-on-surface-variant/30"}`}>
                  {voice.language_code ? voice.language_code.toUpperCase() : "Multilingual"}
                </p>
              </div>
              <span
                className="material-symbols-outlined text-on-surface-variant/30 group-hover:text-primary cursor-pointer"
                onClick={(event) => togglePlay(event, voice)}
              >
                {isPlaying ? "pause_circle" : "play_circle"}
              </span>
            </div>
          );
        })}
        {visibleVoices.length === 0 && (
          <p className="text-xs text-on-surface-variant/40">No voice presets available.</p>
        )}
      </div>
    </section>
  );
}
