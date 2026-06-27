import { AuthGuard } from "@/components/auth/auth-guard";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { DashboardTopbar } from "@/components/dashboard/topbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen bg-muted/30">
        <DashboardSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <DashboardTopbar />
          <main className="relative flex-1">
            <div className="pointer-events-none absolute inset-0 bg-dots opacity-50" />
            <div className="relative mx-auto w-full max-w-7xl px-4 py-8 md:px-8">{children}</div>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
