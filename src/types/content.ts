export interface NavItem {
  title: string;
  href: string;
  filePath?: string;
  children?: NavItem[];
  wip?: boolean;
}

export interface NavModule {
  title: string;
  slug: string;
  /** 1-based position in nav.yml - the number shown in the sidebar and on the home page */
  number: number;
  /** Unnumbered group label from nav.yml (`- track: Name`) */
  track?: string;
  items: NavItem[];
}

export interface NavigationTree {
  modules: NavModule[];
  flatPages: PageRef[];
}

export interface PageRef {
  title: string;
  href: string;
  filePath: string;
  module: string;
  slug: string;
}

export interface PageContent extends PageRef {
  rawContent: string;
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
  module: string;
}
