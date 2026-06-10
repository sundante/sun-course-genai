import { Sidebar } from "@/components/course/Sidebar";
import { MobileNav } from "@/components/course/MobileNav";
import { Header } from "@/components/course/Header";
import { getNavigationTree } from "@/lib/content/nav";

export default function CourseLayout({ children }: { children: React.ReactNode }) {
  const nav = getNavigationTree();

  return (
    <div className="min-h-screen bg-sun-bg overflow-x-hidden">
      <Header />
      <MobileNav nav={nav} />
      <div className="flex">
        <Sidebar nav={nav} />
        <main className="flex-1 min-w-0 px-6 lg:px-8 py-6">
          {children}
        </main>
      </div>
    </div>
  );
}
