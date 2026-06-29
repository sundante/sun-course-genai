import { Header } from "@/components/course/Header";
import { MobileNav } from "@/components/course/MobileNav";
import { Sidebar } from "@/components/course/Sidebar";
import { DisclaimerModal } from "@/components/course/DisclaimerModal";
import { getNavigationTree } from "@/lib/content/nav";

export default function CourseLayout({ children }: { children: React.ReactNode }) {
  const nav = getNavigationTree();
  return (
    <div className="min-h-screen bg-sun-bg overflow-x-hidden">
      <Header />
      <MobileNav nav={nav} />
      <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
        <Sidebar nav={nav} />
        <main className="flex-1 min-w-0 overflow-y-auto flex flex-col">
          {children}
        </main>
      </div>
      <DisclaimerModal />
    </div>
  );
}
