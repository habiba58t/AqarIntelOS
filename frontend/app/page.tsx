


"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { CopilotKit } from "@copilotkit/react-core";
import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { BookOpen, MessageSquare, X, Building, LogIn, BarChart3, Download, Maximize2, Minimize2, MapPin, Home, DollarSign, ArrowRight } from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import { AuthModal } from "@/components/auth/AuthModal";
import { UserProfileDropdown } from "@/components/auth/UserProfileDropdown";
import Image from "next/image";
import { useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { ProjectsMap } from '@/components/ProjectsMap';
import { EnhancedProjectsSection } from '@/components/projectsSection';
import { handleWebpackExternalForEdgeRuntime } from "next/dist/build/webpack/plugins/middleware-plugin";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Project {
  id?: string;
  name: string;
  latitude: number;
  longitude: number;
  location?: string;
  min_price?: number;
  max_price?: number;
  image?: string;
  description?: string;
}

interface project {
  id?: string;
  name: string;
  location: string;
  min_price: number;
  max_price?: number;
  image?: string;
  description?: string;
  developer?: string;
  amenities?: string[];
  payment_plans?: string;
  bedrooms?: string;
  [key: string]: any;
}


interface UserInfo {
  email: string;
  name: string;
  preferredLocations: string[];
  averageBudget: number;
  familySize: number;
  is_investor: boolean;
}

interface AgentState {
  messages?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  saved_plots?: Array<{
    id: string;
    data: any;
  }>;
  user?: UserInfo; 
}

export default function HomePage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [userProfile, setUserProfile] = useState<UserInfo | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  

  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!isAuthenticated || !user?.email) {
        console.log("❌ Not authenticated, skipping profile fetch");
        setUserProfile(null);
        setProfileLoading(false);
        return;
      }

      console.log("🔍 Fetching user profile for:", user.email);
      setProfileLoading(true);

      try {
        const response = await fetch(
          `http://localhost:8000/api/user/profile?email=${encodeURIComponent(user.email)}`
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Successfully fetched user profile:", data);

        const profile: UserInfo = {
          email: user.email,
          name: data.name || user.name || "Guest",
          preferredLocations: Array.isArray(data.preferredLocations)
            ? data.preferredLocations
            : [],
          averageBudget: data.averageBudget || 0,
          familySize: data.familySize || 0,
          is_investor: data.is_investor || false,
        };

        console.log("📦 Processed user profile:", profile);
        setUserProfile(profile);
      } catch (error) {
        console.error("❌ Failed to fetch user profile:", error);
        setUserProfile(null);
      } finally {
        setProfileLoading(false);
      }
    };

    fetchUserProfile();
  }, [isAuthenticated, user?.email]);

  if (authLoading || profileLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
          <p className="text-lg text-gray-700 font-medium">
            {authLoading ? "Authenticating..." : "Loading your profile..."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <HomeContent
        user={user}
        isAuthenticated={isAuthenticated}
        userProfile={userProfile}
      />
    </CopilotKit>
  );
}

function HomeContent({
  user,
  isAuthenticated,
  userProfile,
}: {
  user: any;
  isAuthenticated: boolean;
  userProfile: UserInfo | null;
}) {
  const { state } = useCoAgent<AgentState>({
    name: "policy_qa_agent",
    initialState: {
      saved_plots: [],
      user: userProfile
    }
  });

  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "register">("login");
  const [messages, setMessages] = useState<AgentState["messages"]>([]);
  const [plots, setPlots] = useState<any[]>([]);
  const [isPlotsOpen, setIsPlotsOpen] = useState(true);
  const [isChatFullscreen, setIsChatFullscreen] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [mapProjects, setMapProjects] = useState([]);
  const [searchFilters, setSearchFilters] = useState({
    location: "",
    type: "",
    priceRange: ""
  });

  // ✅ KEY FIX: Use CopilotKit's suggestion system
  useCopilotChatSuggestions({
    instructions: hasInteracted ? "" : "Suggest questions about real estate market analysis, price trends, and property comparisons.",
    minSuggestions: hasInteracted ? 0 : 4,
    maxSuggestions: hasInteracted ? 0 : 4,
  });

  useEffect(() => {
    console.log("🤖 Agent state updated:", state);
    if (state?.user) {
      console.log("✅ User in agent state:", state.user);
    } else {
      console.log("⚠️ No user in agent state");
    }
  }, [state]);

  useEffect(() => {
    if (state?.saved_plots && state.saved_plots.length > 0) {
      setPlots(state.saved_plots);
      setIsPlotsOpen(true);
    }
  }, [state?.saved_plots]);

  useEffect(() => {
    if (state?.messages) {
      setMessages(state.messages);
      // Hide suggestions after first user message
      if (state.messages.some(m => m.role === "user")) {
        setHasInteracted(true);
      }
    }
  }, [state?.messages]);

  // useEffect(() => {
  //   const fetchProjects = async () => {
  //     if (!user) return;

  //     try {
  //       const res = await fetch(`http://127.0.0.1:8000/api/projects/recommended/${encodeURIComponent(user.email)}`);
  //       const data = await res.json();

  //       if (data && Array.isArray(data.recommended_projects)) {
  //         setProjects(data.recommended_projects);
  //       } else {
  //         console.error("Unexpected response format:", data);
  //         setProjects([]);
  //       }
  //     } catch (err) {
  //       console.error("Error fetching projects:", err);
  //       setProjects([]);
  //     } finally {
  //       setLoading(false);
  //     }
  //   };

  //   fetchProjects();
  // }, [user]);

  useEffect(() => {
  fetch('http://localhost:8000/api/projects/map')
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        setMapProjects(data.projects);
      }
    });
}, []);

  const handleChatClick = () => {
    if (!isAuthenticated) {
      setAuthModalMode("login");
      setIsAuthModalOpen(true);
    } else {
      document.getElementById("chat-section")?.scrollIntoView({ behavior: "smooth" });
      setIsChatOpen(true);
    }
  };

  const handleAskAgent = (project: project) => {
    console.log("🤖 User wants to ask about:", project.name);
    
    // Open chat if not open
    if (!isChatOpen) {
      setIsChatOpen(true);
    }

    // Scroll to chat section
    setTimeout(() => {
      document.getElementById("chat-section")?.scrollIntoView({ 
        behavior: "smooth" 
      });
    }, 100);

    // TODO: Optionally inject project context into chat
    // You can use CopilotKit's API to send a message or update context
  };

  const handleSearch = () => {
    // Handle search functionality
    console.log("Search filters:", searchFilters);
    // You can implement search logic here
  };

  const handleNavigation = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ 
      behavior: "smooth" 
    });
  };

  const renderChart = (plotData: any, plotId: string) => {
    if (!plotData) return null;

    try {
      const chartData = typeof plotData === "string" ? JSON.parse(plotData) : plotData;

      return (
        <div className="bg-white rounded-2xl p-6 mt-4 shadow-lg border border-gray-200 hover:shadow-xl transition-all duration-300 group">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <BarChart3 className="w-4 h-4 text-blue-600" />
              </div>
              <h3 className="text-base font-semibold text-gray-800">Market Insights</h3>
            </div>
            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <Download className="w-4 h-4 text-gray-600" />
              </button>
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <Maximize2 className="w-4 h-4 text-gray-600" />
              </button>
            </div>
          </div>
          
          <div
            style={{
              width: "100%",
              height: "320px",
              backgroundColor: "white",
              borderRadius: "12px",
              padding: "12px",
            }}
          >
            <Plot
              data={chartData.data || []}
              layout={{
                ...chartData.layout,
                autosize: true,
                margin: { l: 60, r: 40, b: 70, t: 60, pad: 8 },
                paper_bgcolor: "white",
                plot_bgcolor: "#f8fafc",
                font: {
                  family: "Inter, system-ui, sans-serif",
                  size: 12,
                  color: "#334155",
                },
                title: {
                  text: chartData.layout?.title?.text || "",
                  font: { size: 16, color: "#1e293b", weight: 600 },
                  x: 0.5,
                  xanchor: "center",
                },
                showlegend: chartData.layout?.showlegend !== false,
                legend: {
                  orientation: "h",
                  yanchor: "bottom",
                  y: -0.3,
                  xanchor: "center",
                  x: 0.5,
                  bgcolor: "rgba(255,255,255,0.9)",
                  bordercolor: "#e2e8f0",
                  borderwidth: 1,
                },
                xaxis: {
                  ...chartData.layout?.xaxis,
                  gridcolor: "#f1f5f9",
                  zerolinecolor: "#e2e8f0",
                  linecolor: "#e2e8f0",
                },
                yaxis: {
                  ...chartData.layout?.yaxis,
                  gridcolor: "#f1f5f9",
                  zerolinecolor: "#e2e8f0",
                  linecolor: "#e2e8f0",
                },
              }}
              config={{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ["pan2d", "lasso2d", "select2d"],
                modeBarButtonsToAdd: [],
              }}
              style={{ width: "100%", height: "100%" }}
              useResizeHandler={true}
            />
          </div>
          <div className="mt-4 flex items-center justify-between text-sm">
            <span className="text-gray-500 font-mono">#{plotId.slice(0, 6)}</span>
            <span className="text-blue-600 font-medium flex items-center gap-1">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
              Interactive Analysis
            </span>
          </div>
        </div>
      );
    } catch (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <p className="text-red-700 text-sm font-medium">Chart rendering failed</p>
          </div>
        </div>
      );
    }
  };

  return (
    <>
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />

       {/* LUXURIOUS HERO SECTION WITH PNG BACKGROUND */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-stone-50 via-amber-50 to-stone-100">
  {/* Background Overlays */}
  <div className="absolute inset-0 bg-white/50"></div>
  <div className="absolute inset-0 bg-gradient-to-r from-stone-50/50 to-amber-50/30"></div>
        
        {/* Elegant Texture Overlay */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cpath d=%22M0 0h100v100H0z%22 fill=%22none%22/%3E%3Cpath d=%22M50 50 L100 0 L100 100 L0 100 L0 0 Z%22 fill=%22%23f5f5f4%22 opacity=%220.05%22/%3E%3C/svg%3E')] opacity-40"></div>
        
        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-stone-800 rounded-lg shadow-md">
                  <Building className="w-6 h-6 text-amber-100" />
                </div>
                <span className="text-2xl font-bold text-stone-800 tracking-tight">EstateLux</span>
              </div>
              
              <div className="hidden md:flex items-center gap-10">
                <button 
                  onClick={() => handleNavigation("projects")}
                  className="text-stone-700 hover:text-stone-900 transition-colors font-semibold text-lg"
                >
                  Properties
                </button>
                <button 
                  onClick={() => handleNavigation("map-section")}
                  className="text-stone-700 hover:text-stone-900 transition-colors font-semibold text-lg"
                >
                  Map
                </button>
                <button 
                  onClick={() => handleNavigation("chat-section")}
                  className="text-stone-700 hover:text-stone-900 transition-colors font-semibold text-lg"
                >
                  AI Assistant
                </button>
              </div>

              <div className="flex items-center gap-4">
                {isAuthenticated ? (
                  <UserProfileDropdown />
                ) : (
                  <>
                    <button
                      onClick={() => {
                        setAuthModalMode("login");
                        setIsAuthModalOpen(true);
                      }}
                      className="px-6 py-2.5 text-stone-700 hover:text-stone-900 transition-colors font-semibold text-lg"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => {
                        setAuthModalMode("register");
                        setIsAuthModalOpen(true);
                      }}
                      className="px-8 py-2.5 bg-stone-800 text-amber-50 hover:bg-stone-900 rounded-lg transition-all duration-300 font-semibold text-lg shadow-md hover:shadow-lg transform hover:scale-105"
                    >
                      Get Started
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 max-w-6xl mx-auto px-6 text-center space-y-16">
          {/* Main Heading - Improved Typography */}
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-6xl md:text-8xl font-black text-stone-900 leading-none tracking-tight">
                Your
              </h1>
              <div className="relative inline-block">
                <h1 className="text-6xl md:text-8xl font-black bg-gradient-to-r from-stone-800 to-stone-600 bg-clip-text text-transparent leading-none tracking-tight">
                  Real Estate Guide
                </h1>
                {/* Underline accent */}
                <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 w-32 h-1 bg-amber-500 rounded-full"></div>
              </div>
            </div>
            
            <p className="text-2xl md:text-3xl text-stone-700 max-w-4xl mx-auto leading-relaxed font-semibold tracking-wide">
              Your personal guide to Egypt's finest properties, offering expert insights and tailored recommendations
            </p>
          </div>

          {/* Action Buttons - Replacing Search */}
          <div className="flex flex-col items-center space-y-8">
            {/* Main CTA Buttons */}
            <div className="flex flex-wrap justify-center gap-6">
              <button 
                onClick={() => handleNavigation("projects")}
                className="group px-12 py-4 bg-stone-900 hover:bg-stone-800 text-amber-50 rounded-2xl transition-all duration-300 font-bold text-lg shadow-2xl hover:shadow-3xl transform hover:scale-105 flex items-center gap-3"
              >
                Browse Projects
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button 
                onClick={handleChatClick}
                className="group px-12 py-4 bg-white/90 hover:bg-white border-2 border-stone-300 hover:border-stone-400 text-stone-800 rounded-2xl transition-all duration-300 font-bold text-lg shadow-xl hover:shadow-2xl backdrop-blur-sm transform hover:scale-105 flex items-center gap-3"
              >
                <MessageSquare className="w-5 h-5" />
                AI Agent
              </button>
            </div>
            <button 
                onClick={() => handleNavigation("projects")}
                className="group px-12 py-4 bg-white/90 hover:bg-white border-2 border-stone-300 hover:border-stone-400 text-stone-800 rounded-2xl transition-all duration-300 font-bold text-lg shadow-xl hover:shadow-2xl backdrop-blur-sm transform hover:scale-105 flex items-center gap-3"
              >
                <MapPin className="w-5 h-5" />
                Interactive Map
              </button>
            </div>

          

          </div>

        
      </section>

      {/* RECOMMENDED PROJECTS */}
      {/* <section id="projects" className="py-20 bg-white text-center">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-6 text-gray-900">
            Projects For You
          </h2>
          <p className="text-gray-600 mb-10">
            Discover trending real estate developments based on current market
            insights.
          </p>

          {loading ? (
            <p className="text-gray-500">Loading projects...</p>
          ) : projects.length === 0 ? (
            <p className="text-gray-500">No projects available at the moment.</p>
          ) : (
            <div className="grid md:grid-cols-3 gap-8">
              {projects.map((p, i) => (
                <div
                  key={i}
                  className="rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all bg-white"
                >
                  <Image
                    src={p.image?.startsWith("http") ? p.image : "/images/default-project.jpg"}
                    alt={p.name}
                    width={400}
                    height={250}
                    className="w-full h-56 object-cover"
                  />
                  <div className="p-4 text-left">
                    <h3 className="text-lg font-semibold text-gray-800">
                      {p.name}
                    </h3>
                    <p className="text-sm text-gray-500">{p.location}</p>
                    <p className="text-primary font-bold mt-2">
                      {p.min_price
                        ? `${Number(p.min_price).toLocaleString()} EGP`
                        : "N/A"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section> */}

      <EnhancedProjectsSection
        userProfile={userProfile}
        onAskAgent={handleAskAgent}
      />


{ /* MAP SECTION */}
      <section id="map-section" className="py-20 bg-white">
  <div className="max-w-6xl mx-auto px-6">
    <h2 className="text-3xl font-bold mb-6 text-gray-900 text-center">
      Explore Projects on Map
    </h2>
    <p className="text-gray-600 mb-10 text-center">
      Interactive map showing all available real estate projects
    </p>
    
    <ProjectsMap
      projects={mapProjects}
      center={[30.0444, 31.2357]}
      zoom={11}
      height="600px"
      onProjectClick={(project) => {
        console.log('Clicked:', project);
        // Handle click - maybe scroll to project details
      }}
    />
  </div>
</section>

      {/* ENHANCED CHAT SECTION */}
      <section
        id="chat-section"
        className={`min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 text-gray-900 flex flex-col ${
          isChatFullscreen ? "fixed inset-0 z-50" : "relative"
        }`}
      >
        {isChatOpen && isAuthenticated ? (
          <div className="flex flex-col flex-1 h-full">
            {/* Enhanced Header */}
            <div className="bg-white border-b border-gray-200 shadow-sm py-4 px-6">
              <div className="max-w-7xl mx-auto flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-primary to-blue-700 rounded-xl shadow-lg">
                    <Building className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">Real Estate AI Assistant</h2>
                    <p className="text-sm text-gray-600">Powered by advanced market intelligence</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsChatFullscreen(!isChatFullscreen)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
                    title={isChatFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                  >
                    {isChatFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                  </button>
                  <UserProfileDropdown />
                  <button
                    onClick={() => setIsChatOpen(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex overflow-hidden bg-white">
              {/* Chat Panel */}
              <div
                className={`overflow-y-auto transition-all duration-300 ${
                  plots.length > 0 && isPlotsOpen
                    ? "flex-1 border-r border-gray-200"
                    : "w-full"
                }`}
              >
                <div className="max-w-4xl mx-auto p-6 h-full">
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                    <CopilotChat
                      labels={{
                        initial:
                          "Hello! I'm your Real Estate Assistant. I can help you analyze properties, market trends, and generate visual insights. What would you like to know?",
                      }}
                      className="w-full"
                    />
                  </div>
                </div>
              </div>

              {/* Visual Insights Panel */}
              {plots.length > 0 && (
                <div
                  className={`relative bg-white border-l border-gray-200 transition-all duration-300 ${
                    isPlotsOpen ? "w-2/5" : "w-16"
                  }`}
                >
                  <button
                    onClick={() => setIsPlotsOpen(!isPlotsOpen)}
                    className="absolute top-6 -left-4 z-10 p-3 bg-primary rounded-full shadow-lg hover:bg-blue-800 transition-all border-2 border-white"
                  >
                    {isPlotsOpen ? (
                      <X className="w-4 h-4 text-white" />
                    ) : (
                      <BarChart3 className="w-4 h-4 text-white" />
                    )}
                  </button>

                  {isPlotsOpen && (
                    <div className="h-full flex flex-col">
                      {/* Insights Header */}
                      <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-blue-50/30">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/10 rounded-lg">
                              <BarChart3 className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900">Visual Insights</h3>
                              <p className="text-sm text-gray-600">
                                {plots.length} {plots.length === 1 ? "chart" : "charts"} generated
                              </p>
                            </div>
                          </div>
                          {plots.length > 0 && (
                            <button
                              onClick={() => setPlots([])}
                              className="text-sm text-red-600 hover:text-red-700 transition-colors px-3 py-1 rounded-lg hover:bg-red-50"
                            >
                              Clear all
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Insights Content */}
                      <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {plots.map((plot, index) => (
                          <div
                            key={plot.id || index}
                            className="group relative"
                          >
                            {renderChart(plot.data, plot.id)}
                          </div>
                        ))}
                      </div>

                      {/* Insights Footer */}
                      <div className="p-4 border-t border-gray-200 bg-gray-50">
                        <p className="text-xs text-gray-600 text-center">
                          Charts update in real-time based on your conversation
                        </p>
                      </div>
                    </div>
                  )}

                  {!isPlotsOpen && (
                    <div className="h-full flex items-center justify-center">
                      <div className="transform -rotate-90 whitespace-nowrap text-xs text-gray-500 font-semibold tracking-wider">
                        INSIGHTS ({plots.length})
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Enhanced Footer */}
            <div className="bg-white border-t border-gray-200 py-3 px-6">
              <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-4 text-gray-600">
                    <span className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      AI Assistant Online
                    </span>
                    <span>•</span>
                    <span>Real-time market data</span>
                  </div>
                  <div className="text-gray-500">
                    Try asking about prices, trends, or market analysis
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center flex-1 text-center space-y-6 p-8">
            <div className="p-6 bg-white rounded-2xl shadow-lg border border-gray-200 max-w-md">
              <div className="w-16 h-16 bg-gradient-to-br from-primary to-blue-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Start a Conversation</h3>
              <p className="text-gray-600 mb-6">
                {isAuthenticated
                  ? "Chat with our AI assistant to get personalized real estate insights and visual analysis."
                  : "Sign in to access our AI-powered real estate assistant and market insights."}
              </p>
              {!isAuthenticated ? (
                <button
                  onClick={() => {
                    setAuthModalMode("login");
                    setIsAuthModalOpen(true);
                  }}
                  className="w-full px-6 py-3 bg-primary text-white rounded-xl hover:bg-blue-900 transition-all font-semibold shadow-lg hover:shadow-xl"
                >
                  Sign In to Continue
                </button>
              ) : (
                <button
                  onClick={handleChatClick}
                  className="w-full px-6 py-3 bg-primary text-white rounded-xl hover:bg-blue-900 transition-all font-semibold shadow-lg hover:shadow-xl"
                >
                  Open AI Assistant
                </button>
              )}
            </div>
          </div>
        )}
      </section>

      {/* FOOTER */}
      <footer className="bg-slate-900 text-white py-8 text-center">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-sm text-slate-400">
            © {new Date().getFullYear()} Real Estate Assistant — Powered by
            CopilotKit AI
          </p>
        </div>
      </footer>
    </>
  );
}

















