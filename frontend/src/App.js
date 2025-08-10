import React, { useState } from 'react';
import './App.css';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Copy, Wand2, Sparkles, FileText, Settings } from 'lucide-react';
import { toast } from 'sonner';

function App() {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async () => {
    if (!command.trim()) {
      toast.error('Please enter a command');
      return;
    }

    setLoading(true);
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
      const response = await fetch(`${backendUrl}/api/generate-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command: command.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate prompt');
      }

      const data = await response.json();
      setResult(data);
      toast.success('Prompt generated successfully!');
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message || 'Failed to generate prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text, type) => {
    navigator.clipboard.writeText(text);
    toast.success(`${type} copied to clipboard!`);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleGenerate();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-50 to-zinc-100">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Wand2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Prompt Engineer</h1>
                <p className="text-sm text-gray-600">Transform simple commands into powerful AI prompts</p>
              </div>
            </div>
            <Badge variant="outline" className="hidden sm:flex items-center space-x-1">
              <Sparkles className="w-3 h-3" />
              <span>Powered by AI</span>
            </Badge>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Input Section */}
        <div className="mb-8">
          <Card className="border-0 shadow-lg bg-white/70 backdrop-blur-sm">
            <CardHeader className="text-center pb-4">
              <CardTitle className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                World-Class Prompt Engineering
              </CardTitle>
              <CardDescription className="text-lg text-gray-600 max-w-2xl mx-auto">
                Enter a simple command and watch it transform into a detailed, professional prompt that can be used with any AI agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
                <Input
                  placeholder="e.g., Write a blog post about AI, Create a marketing strategy, Analyze data..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="flex-1 h-12 text-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
                />
                <Button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="h-12 px-8 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4 mr-2" />
                      Generate Prompt
                    </>
                  )}
                </Button>
              </div>
              
              {/* Example Commands */}
              <div className="pt-4">
                <p className="text-sm text-gray-500 mb-3">Try these examples:</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    "Write a product description",
                    "Create a meeting agenda",
                    "Analyze customer feedback",
                    "Generate social media content"
                  ].map((example) => (
                    <Button
                      key={example}
                      variant="outline"
                      size="sm"
                      onClick={() => setCommand(example)}
                      className="text-xs hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
                    >
                      {example}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Section */}
        {result && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Generated Prompts</h2>
              <Badge className="bg-green-100 text-green-800 border-green-200">
                ✨ Ready to Use
              </Badge>
            </div>

            <Tabs defaultValue="structured" className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-gray-100">
                <TabsTrigger value="structured" className="flex items-center space-x-2">
                  <FileText className="w-4 h-4" />
                  <span>Structured Prompt</span>
                </TabsTrigger>
                <TabsTrigger value="system" className="flex items-center space-x-2">
                  <Settings className="w-4 h-4" />
                  <span>System Prompt</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="structured" className="mt-4">
                <Card className="border-0 shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                      <CardTitle className="text-lg">Structured Prompt</CardTitle>
                      <CardDescription>
                        Organized format with clear sections and guidelines
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopy(result.structured_prompt, 'Structured prompt')}
                      className="hover:bg-gray-50"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-indigo-500">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                        {result.structured_prompt}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="system" className="mt-4">
                <Card className="border-0 shadow-lg">
                  <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                      <CardTitle className="text-lg">System Prompt</CardTitle>
                      <CardDescription>
                        Technical format suitable for AI model system messages
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopy(result.system_prompt, 'System prompt')}
                      className="hover:bg-gray-50"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-purple-500">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
                        {result.system_prompt}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Metadata */}
            <Card className="border-0 shadow-sm bg-gray-50/50">
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Original Command: <span className="font-medium text-gray-900">"{result.command}"</span></span>
                  </div>
                  <div className="text-sm text-gray-500">
                    Generated: {new Date(result.created_at).toLocaleString()}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Features Section */}
        {!result && (
          <div className="mt-16">
            <Card className="border-0 shadow-lg bg-gradient-to-r from-indigo-50 to-purple-50">
              <CardContent className="pt-8">
                <h3 className="text-2xl font-bold text-center mb-8 text-gray-900">
                  Transform Any Command Into Professional Prompts
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <FileText className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold mb-2">Structured Format</h4>
                    <p className="text-sm text-gray-600">
                      Get organized prompts with clear sections, context, and guidelines
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Settings className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold mb-2">System Ready</h4>
                    <p className="text-sm text-gray-600">
                      Technical format perfect for AI model system messages
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Copy className="w-6 h-6 text-white" />
                    </div>
                    <h4 className="font-semibold mb-2">One-Click Copy</h4>
                    <p className="text-sm text-gray-600">
                      Instantly copy prompts to use in any AI application
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white/80 backdrop-blur-sm mt-16">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="text-center text-gray-600">
            <p className="text-sm">
              © 2025 AI Prompt Engineer - Transform simple commands into powerful AI prompts
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;