export interface Citation {
  id?: string;
  source: string;
  page?: number;
  text: string;
  score?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}
