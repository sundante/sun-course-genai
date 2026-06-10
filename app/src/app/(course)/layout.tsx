import { Sidebar } from "@/components/course/Sidebar";
import { Header } from "@/components/course/Header";
import { getNavigationTree } from "@/lib/content/nav";

export default function CourseLayout({ children }: { children: React.ReactNode }) {
  const nav = getNavigationTree();

  return (
    <div className="min-h-screen bg-sun-bg">
      <Header />
      <div className="flex">
        <Sidebar nav={nav} />
        <main className="flex-1 min-w-0 px-6 py-8 max-w-4xl mx-auto lg:ml-0">
          {children}
        </main>
      </div>
    </div>
  );
}
