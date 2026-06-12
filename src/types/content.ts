export interface NavItem {
  title: string;
  /** URL path like /learn/llm-models/01-llm-fundamentals */
  href: string;
  /** Relative path from docs/ e.g. 01-LLM-Models/Notes/01-LLM-Fundamentals.md */
  filePath?: string;
  children?: NavItem[];
}

export interface NavModule {
  title: string;
  /** slug like llm-models */
  slug: string;
  items: NavItem[];
}

export interface NavigationTree {
  modules: NavModule[];
  /** Flat ordered list of all leaf pages for prev/next navigation */
  flatPages: PageRef[];
}

export interface PageRef {
  title: string;
  href: string;
  filePath: string;
  module: string;
  slug: string;
}

export interface PageContent {
  title: string;
  href: string;
  filePath: string;
  module: string;
  slug: string;
  rawContent: string;
  /** Extracted headings for table of contents */
  toc: TocItem[];
}

export interface TocItem {
  id: string;
  text: string;
  level: number;
}

export interface QuizCard {
  question: string;
  answer: string;
  difficulty?: "Easy" | "Medium" | "Hard";
  module: string;
  moduleTitle: string;
}
