// components/EnhancedProjectsSection.tsx
"use client";

import React, { useState, useEffect } from 'react';
import { X, MapPin, DollarSign, Home, MessageSquare, ExternalLink, ChevronRight, Filter, Loader2 } from 'lucide-react';
import Image from 'next/image';

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

interface UserProfile {
  preferredLocations?: string[];
  averageBudget?: number;
}

interface EnhancedProjectsSectionProps {
  userProfile: UserProfile | null;
  onAskAgent?: (project: project) => void;
}

export function EnhancedProjectsSection({ 
  userProfile, 
  onAskAgent 
}: EnhancedProjectsSectionProps) {
  const [projects, setProjects] = useState<project[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<project | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  // Filter states
  const [locationFilter, setLocationFilter] = useState<string[]>([]);
  const [maxBudget, setMaxBudget] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Fetch projects from backend
  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      try {
        const response = await fetch('http://127.0.0.1:8000/api/projects/all');
        const data = await response.json();
        
        if (data.success && Array.isArray(data.projects)) {
          console.log(`✅ Fetched ${data.projects.length} projects`);
          setProjects(data.projects);
        } else {
          console.error('Invalid response:', data);
          setProjects([]);
        }
      } catch (error) {
        console.error('Error fetching projects:', error);
        setProjects([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  // Apply filters based on user preferences and selected filters
  useEffect(() => {
    let filtered = [...projects];

    // Filter by locations (user preference or manual selection)
    const locationsToFilter = locationFilter.length > 0 
      ? locationFilter 
      : userProfile?.preferredLocations || [];

    if (locationsToFilter.length > 0) {
      filtered = filtered.filter(project =>
        locationsToFilter.some(loc => 
          project.location?.toLowerCase().includes(loc.toLowerCase())
        )
      );
    }

    // Filter by budget (user budget or manual selection)
    const budgetToFilter = maxBudget || userProfile?.averageBudget;
    
    if (budgetToFilter) {
      filtered = filtered.filter(project => 
        project.min_price <= budgetToFilter
      );
    }

    // Sort by relevance (closest to budget, preferred locations)
    filtered.sort((a, b) => {
      const aInPreferred = userProfile?.preferredLocations?.some(loc =>
        a.location?.toLowerCase().includes(loc.toLowerCase())
      ) ? 1 : 0;
      
      const bInPreferred = userProfile?.preferredLocations?.some(loc =>
        b.location?.toLowerCase().includes(loc.toLowerCase())
      ) ? 1 : 0;

      // Prioritize preferred locations
      if (aInPreferred !== bInPreferred) {
        return bInPreferred - aInPreferred;
      }

      // Then sort by price proximity to budget
      if (budgetToFilter) {
        const aDiff = Math.abs(a.min_price - budgetToFilter);
        const bDiff = Math.abs(b.min_price - budgetToFilter);
        return aDiff - bDiff;
      }

      return 0;
    });

    setFilteredProjects(filtered);
  }, [projects, locationFilter, maxBudget, userProfile]);

  // Get unique locations for filter
  const availableLocations = Array.from(
    new Set(projects.map(p => p.location).filter(Boolean))
  );

  const handleViewDetails = (project: project) => {
    setSelectedProject(project);
    setIsSidebarOpen(true);
  };

  const handleAskAgent = (project: project) => {
    if (onAskAgent) {
      onAskAgent(project);
    }
    // Close sidebar
    setIsSidebarOpen(false);
  };

  if (loading) {
    return (
      <section id="projects" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mb-4" />
            <p className="text-gray-600">Loading projects...</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <>
      <section id="projects" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          {/* Header with Filters */}
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold mb-4 text-gray-900">
              {userProfile?.preferredLocations && userProfile.preferredLocations.length > 0
                ? 'Projects in Your Preferred Areas'
                : 'Recommended Projects For You'}
            </h2>
            <p className="text-gray-600 mb-6">
              {filteredProjects.length} {filteredProjects.length === 1 ? 'property' : 'properties'} matching your preferences
            </p>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <Filter className="w-4 h-4" />
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="bg-gray-50 rounded-xl p-6 mb-8 border border-gray-200">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Location Filter */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Filter by Location
                  </label>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {availableLocations.length > 0 ? (
                      availableLocations.map((location) => (
                        <label key={location} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={locationFilter.includes(location)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setLocationFilter([...locationFilter, location]);
                              } else {
                                setLocationFilter(locationFilter.filter(l => l !== location));
                              }
                            }}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-700">{location}</span>
                        </label>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No locations available</p>
                    )}
                  </div>
                </div>

                {/* Budget Filter */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Maximum Budget (EGP)
                  </label>
                  <input
                    type="number"
                    value={maxBudget || ''}
                    onChange={(e) => setMaxBudget(e.target.value ? parseInt(e.target.value) : null)}
                    placeholder={userProfile?.averageBudget?.toLocaleString() || 'Enter budget'}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    {userProfile?.averageBudget 
                      ? `Your saved budget: ${userProfile.averageBudget.toLocaleString()} EGP`
                      : 'Set your budget to see matching properties'}
                  </p>
                </div>
              </div>

              {/* Clear Filters */}
              {(locationFilter.length > 0 || maxBudget) && (
                <button
                  onClick={() => {
                    setLocationFilter([]);
                    setMaxBudget(null);
                  }}
                  className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Clear all filters
                </button>
              )}
            </div>
          )}

          {/* Projects Grid */}
          {filteredProjects.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-xl">
              <Home className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 font-medium">No projects match your criteria</p>
              <p className="text-sm text-gray-500 mt-2">Try adjusting your filters or exploring all projects</p>
              {(locationFilter.length > 0 || maxBudget) && (
                <button
                  onClick={() => {
                    setLocationFilter([]);
                    setMaxBudget(null);
                  }}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold"
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-8">
              {filteredProjects.map((project, index) => (
                <div
                  key={project.id || index}
                  className="rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all bg-white border border-gray-200 group"
                >
                  {/* Project Image */}
                  <div className="relative h-56 overflow-hidden bg-gray-200">
                    <Image
                      src={project.image?.startsWith('http') ? project.image : '/images/default-project.jpg'}
                      alt={project.name}
                      width={400}
                      height={250}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                    />
                    {/* Price Badge */}
                    <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-full">
                      <p className="text-blue-600 font-bold text-sm">
                        {(project.min_price / 1000000).toFixed(1)}M EGP
                      </p>
                    </div>
                  </div>

                  {/* Project Details */}
                  <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-1">
                      {project.name}
                    </h3>
                    
                    <div className="flex items-center gap-1 text-gray-600 mb-3">
                      <MapPin className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm line-clamp-1">{project.location}</span>
                    </div>

                    {/* Brief Description */}
                    {project.description && (
                      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                        {project.description}
                      </p>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetails(project)}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold flex items-center justify-center gap-1"
                      >
                        View Details
                        <ChevronRight className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => handleAskAgent(project)}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors group/btn"
                        title="Ask AI Agent"
                      >
                        <MessageSquare className="w-4 h-4 text-gray-700 group-hover/btn:text-blue-600" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Project Details Sidebar */}
      {isSidebarOpen && selectedProject && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity"
            onClick={() => setIsSidebarOpen(false)}
          />

          {/* Sidebar */}
          <div className="fixed right-0 top-0 bottom-0 w-full md:w-[500px] bg-white shadow-2xl z-50 overflow-y-auto transform transition-transform">
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 z-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  Project Details
                </h2>
                <button
                  onClick={() => setIsSidebarOpen(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6 text-gray-600" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {/* Project Image */}
              <div className="rounded-xl overflow-hidden bg-gray-200">
                <Image
                  src={selectedProject.image?.startsWith('http') ? selectedProject.image : '/images/default-project.jpg'}
                  alt={selectedProject.name}
                  width={500}
                  height={300}
                  className="w-full h-64 object-cover"
                />
              </div>

              {/* Project Name */}
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {selectedProject.name}
                </h3>
                <div className="flex items-center gap-2 text-gray-600">
                  <MapPin className="w-5 h-5" />
                  <span className="text-lg">{selectedProject.location}</span>
                </div>
              </div>

              {/* Price */}
              <div className="bg-blue-50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-semibold text-gray-700">Price Range</span>
                </div>
                <p className="text-2xl font-bold text-blue-600">
                  {(selectedProject.min_price / 1000000).toFixed(1)}M EGP
                  {selectedProject.max_price && (
                    <span className="text-lg text-gray-600 font-normal">
                      {' '}- {(selectedProject.max_price / 1000000).toFixed(1)}M EGP
                    </span>
                  )}
                </p>
              </div>

              {/* Description */}
              {selectedProject.description && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Description</h4>
                  <p className="text-gray-600 leading-relaxed">
                    {selectedProject.description}
                  </p>
                </div>
              )}

              {/* Developer */}
              {selectedProject.developer && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Developer</h4>
                  <p className="text-gray-600">{selectedProject.developer}</p>
                </div>
              )}

              {/* Amenities */}
              {selectedProject.amenities && selectedProject.amenities.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">Amenities</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {selectedProject.amenities.map((amenity: string, index: number) => (
                      <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        {amenity}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Payment Plans */}
              {selectedProject.payment_plans && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Payment Plans</h4>
                  <p className="text-gray-600">{selectedProject.payment_plans}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="sticky bottom-0 bg-white border-t border-gray-200 pt-6 mt-6 space-y-3">
                <button
                  onClick={() => handleAskAgent(selectedProject)}
                  className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-semibold flex items-center justify-center gap-2"
                >
                  <MessageSquare className="w-5 h-5" />
                  Ask AI Agent About This Project
                </button>
                
                {selectedProject.website && (
                  <a
                    href={selectedProject.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full px-6 py-3 bg-gray-100 text-gray-900 rounded-xl hover:bg-gray-200 transition-colors font-semibold flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-5 h-5" />
                    Visit Official Website
                  </a>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

export default EnhancedProjectsSection;