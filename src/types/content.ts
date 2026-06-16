export interface NavItem {
  title: string;
  href: string;
  filePath?: string;
  children?: NavItem[];
}

export interface NavModule {
  title: string;
  slug: string;
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
