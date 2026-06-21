export type Message = {
  role: "user" | "assistant";
  content: string;
};

export type Thread = {
  id: string;
  title: string;
  timestamp: number;
  pinned?: boolean;
  projectId?: string;
};

export type Project = {
  id: string;
  name: string;
  timestamp: number;
};

export type Document = {
  filename: string;
  size_bytes: number;
  chunks_count: number;
  status: string;
  thread_id?: string;
};

export type QuickPrompt = {
  title: string;
  desc: string;
  text: string;
  docKeywords: string[];
};
