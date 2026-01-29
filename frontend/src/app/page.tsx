import type { ComponentType } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Upload, BarChart3, Route, ArrowRight } from "lucide-react";
import { PublicHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      <PublicHeader />

      {/* Hero */}
      <main className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
            Transform Project Transcripts into{" "}
            <span className="text-primary">Visual Dependencies</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Upload your project transcripts, let AI extract tasks and dependencies,
            and visualize your workflow with interactive graphs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="px-8">
                Start Free <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
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
          <h2 className="text-3xl font-bold text-foreground text-center mb-12">
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
      <footer className="border-t border-border mt-20">
        <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">
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
  icon: ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <Card className="transition-colors">
      <CardHeader className="pb-3">
        <div className="rounded-lg bg-primary/10 w-12 h-12 flex items-center justify-center">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
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
      <div className="w-12 h-12 rounded-full bg-primary text-primary-foreground font-bold text-lg flex items-center justify-center mx-auto mb-4">
        {number}
      </div>
      <h4 className="text-lg font-semibold text-foreground mb-1">{title}</h4>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
