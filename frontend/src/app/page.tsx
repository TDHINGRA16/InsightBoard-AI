import Link from "next/link";
import { Button } from "@/components/ui/button";
import { GitBranch, Upload, BarChart3, Route, ArrowRight } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50">
        <div className="container mx-auto flex items-center justify-between h-16 px-4">
          <div className="flex items-center gap-2">
            <GitBranch className="h-8 w-8 text-cyan-400" />
            <span className="font-bold text-xl text-white">InsightBoard</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" className="text-slate-300 hover:text-white">
                Sign In
              </Button>
            </Link>
            <Link href="/signup">
              <Button className="bg-cyan-500 hover:bg-cyan-600 text-white">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Transform Project Transcripts into{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
              Visual Dependencies
            </span>
          </h1>
          <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Upload your project transcripts, let AI extract tasks and dependencies,
            and visualize your workflow with interactive graphs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button
                size="lg"
                className="bg-cyan-500 hover:bg-cyan-600 text-white px-8"
              >
                Start Free <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/login">
              <Button
                size="lg"
                variant="outline"
                className="border-slate-600 text-slate-300 hover:bg-slate-800"
              >
                Sign In
              </Button>
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-24">
          <FeatureCard
            icon={Upload}
            title="Upload Transcripts"
            description="Upload .txt or .pdf project transcripts and let our AI analyze them automatically."
          />
          <FeatureCard
            icon={Route}
            title="Extract Dependencies"
            description="AI-powered extraction of tasks and their dependencies with critical path analysis."
          />
          <FeatureCard
            icon={BarChart3}
            title="Visualize & Export"
            description="Interactive React Flow graphs with export options for JSON, CSV, and Gantt charts."
          />
        </div>

        {/* How It Works */}
        <div className="mt-32">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            <Step number={1} title="Upload" description="Drop your transcript file" />
            <Step number={2} title="Analyze" description="AI extracts tasks & deps" />
            <Step number={3} title="Visualize" description="View interactive graph" />
            <Step number={4} title="Export" description="Download in any format" />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 mt-20">
        <div className="container mx-auto px-4 py-8 text-center text-slate-500">
          <p>&copy; {new Date().getFullYear()} InsightBoard. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: any;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 hover:border-cyan-500/50 transition-colors">
      <div className="rounded-lg bg-cyan-500/10 w-12 h-12 flex items-center justify-center mb-4">
        <Icon className="h-6 w-6 text-cyan-400" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-slate-400">{description}</p>
    </div>
  );
}

function Step({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-cyan-500 text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">
        {number}
      </div>
      <h4 className="text-lg font-semibold text-white mb-1">{title}</h4>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  );
}
