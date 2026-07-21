export interface ParsedScriptRow {
  row_index: number;
  external_id: string | null;
  title: string | null;
  script_text: string;
  notes: string | null;
  language_hint: string | null;
  voice_hint: string | null;
  detected_language_code: string | null;
  is_valid: boolean;
  validation_error: string | null;
}

export interface ColumnDetection {
  id: string | null;
  title: string | null;
  script: string | null;
  language: string | null;
  voice: string | null;
  notes: string | null;
}

export interface UploadResponse {
  upload_token: string;
  columns_detected: ColumnDetection;
  rows: ParsedScriptRow[];
  total_rows: number;
  valid_rows: number;
  warnings: string[];
}
