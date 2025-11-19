// // components/ProjectsMap.tsx
// "use client";

// import React, { useEffect, useRef, useState } from 'react';
// import { MapPin, X, Navigation, Maximize2, Minimize2 } from 'lucide-react';

// interface Project {
//   id?: string;
//   name: string;
//   latitude: number;
//   longitude: number;
//   location?: string;
//   min_price?: number;
//   max_price?: number;
//   image?: string;
//   description?: string;
// }

// interface ProjectsMapProps {
//   projects?: Project[];
//   center?: [number, number]; // [lat, lng]
//   zoom?: number;
//   height?: string;
//   onProjectClick?: (project: Project) => void;
// }

// export function ProjectsMap({
//   projects = [],
//   center = [30.0444, 31.2357], // Cairo, Egypt default
//   zoom = 11,
//   height = '600px',
//   onProjectClick
// }: ProjectsMapProps) {
//   const mapRef = useRef<HTMLDivElement>(null);
//   const mapInstanceRef = useRef<any>(null);
//   const markersRef = useRef<any[]>([]);
  
//   const [selectedProject, setSelectedProject] = useState<Project | null>(null);
//   const [isFullscreen, setIsFullscreen] = useState(false);
//   const [userLocation, setUserLocation] = useState<[number, number] | null>(null);

//   // Load Leaflet dynamically (client-side only)
//   useEffect(() => {
//     if (typeof window === 'undefined') return;

//     const loadLeaflet = async () => {
//       // Dynamically import Leaflet CSS
//       const link = document.createElement('link');
//       link.rel = 'stylesheet';
//       link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
//       document.head.appendChild(link);

//       // Wait for Leaflet to load
//       const L = await import('leaflet');
      
//       // Fix default marker icon issue in Next.js
//       delete (L.Icon.Default.prototype as any)._getIconUrl;
//       L.Icon.Default.mergeOptions({
//         iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
//         iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
//         shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
//       });

//       if (!mapRef.current || mapInstanceRef.current) return;

//       // Initialize map
//       const map = L.map(mapRef.current).setView(center, zoom);

//       // Add OpenStreetMap tiles (completely free)
//       L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//         attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
//         maxZoom: 19,
//       }).addTo(map);

//       mapInstanceRef.current = map;

//       // Add custom CSS for markers
//       const style = document.createElement('style');
//       style.textContent = `
//         .custom-marker {
//           background-color: #2563eb;
//           border: 3px solid white;
//           border-radius: 50%;
//           width: 30px;
//           height: 30px;
//           display: flex;
//           align-items: center;
//           justify-content: center;
//           box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
//           cursor: pointer;
//           transition: transform 0.2s;
//         }
//         .custom-marker:hover {
//           transform: scale(1.2);
//           background-color: #1d4ed8;
//         }
//         .custom-marker svg {
//           width: 18px;
//           height: 18px;
//           color: white;
//         }
//       `;
//       document.head.appendChild(style);
//     };

//     loadLeaflet();

//     return () => {
//       if (mapInstanceRef.current) {
//         mapInstanceRef.current.remove();
//         mapInstanceRef.current = null;
//       }
//     };
//   }, []);

//   // Add markers when projects change
//   useEffect(() => {
//     if (!mapInstanceRef.current || !projects.length) return;

//     const L = require('leaflet');

//     // Clear existing markers
//     markersRef.current.forEach(marker => marker.remove());
//     markersRef.current = [];

//     // Add markers for each project
//     projects.forEach((project) => {
//       if (!project.latitude || !project.longitude) return;

//       // Create custom icon
//       const customIcon = L.divIcon({
//         className: 'custom-div-icon',
//         html: `
//           <div class="custom-marker">
//             <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
//               <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
//               <circle cx="12" cy="10" r="3"/>
//             </svg>
//           </div>
//         `,
//         iconSize: [30, 30],
//         iconAnchor: [15, 30],
//         popupAnchor: [0, -30],
//       });

//       const marker = L.marker([project.latitude, project.longitude], {
//         icon: customIcon,
//       }).addTo(mapInstanceRef.current);

//       // Create popup content
//       const popupContent = `
//         <div style="min-width: 200px;">
//           <h3 style="font-weight: bold; font-size: 16px; margin-bottom: 8px; color: #1e293b;">
//             ${project.name}
//           </h3>
//           ${project.location ? `<p style="color: #64748b; font-size: 14px; margin-bottom: 4px;">📍 ${project.location}</p>` : ''}
//           ${project.min_price ? `
//             <p style="color: #2563eb; font-weight: 600; font-size: 14px;">
//               💰 ${(project.min_price / 1000000).toFixed(1)}M EGP
//               ${project.max_price ? ` - ${(project.max_price / 1000000).toFixed(1)}M` : ''}
//             </p>
//           ` : ''}
//           <button 
//             onclick="window.handleProjectClick('${project.id || project.name}')"
//             style="
//               margin-top: 8px;
//               padding: 6px 12px;
//               background-color: #2563eb;
//               color: white;
//               border: none;
//               border-radius: 6px;
//               cursor: pointer;
//               font-size: 14px;
//               width: 100%;
//             "
//           >
//             View Details
//           </button>
//         </div>
//       `;

//       marker.bindPopup(popupContent);

//       // Click handler
//       marker.on('click', () => {
//         setSelectedProject(project);
//         if (onProjectClick) {
//           onProjectClick(project);
//         }
//       });

//       markersRef.current.push(marker);
//     });

//     // Fit map to show all markers
//     if (projects.length > 0) {
//       const group = L.featureGroup(markersRef.current);
//       mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
//     }
//   }, [projects, onProjectClick]);

//   // Get user location
//   const getUserLocation = () => {
//     if (navigator.geolocation) {
//       navigator.geolocation.getCurrentPosition(
//         (position) => {
//           const userLoc: [number, number] = [
//             position.coords.latitude,
//             position.coords.longitude,
//           ];
//           setUserLocation(userLoc);

//           if (mapInstanceRef.current) {
//             const L = require('leaflet');
            
//             // Add user location marker
//             const userIcon = L.divIcon({
//               className: 'user-location-marker',
//               html: `
//                 <div style="
//                   background-color: #10b981;
//                   border: 3px solid white;
//                   border-radius: 50%;
//                   width: 20px;
//                   height: 20px;
//                   box-shadow: 0 0 0 8px rgba(16, 185, 129, 0.2);
//                 "></div>
//               `,
//               iconSize: [20, 20],
//               iconAnchor: [10, 10],
//             });

//             L.marker(userLoc, { icon: userIcon })
//               .addTo(mapInstanceRef.current)
//               .bindPopup('📍 Your Location')
//               .openPopup();

//             mapInstanceRef.current.setView(userLoc, 13);
//           }
//         },
//         (error) => {
//           console.error('Error getting location:', error);
//           alert('Unable to get your location. Please enable location services.');
//         }
//       );
//     }
//   };

//   // Toggle fullscreen
//   const toggleFullscreen = () => {
//     setIsFullscreen(!isFullscreen);
//   };

//   return (
//     <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
//       {/* Map Container */}
//       <div
//         ref={mapRef}
//         style={{ height: isFullscreen ? '100vh' : height }}
//         className="rounded-xl shadow-lg overflow-hidden border border-gray-200"
//       />

//       {/* Controls Overlay */}
//       <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
//         <button
//           onClick={getUserLocation}
//           className="p-3 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
//           title="Get my location"
//         >
//           <Navigation className="w-5 h-5 text-gray-700" />
//         </button>
        
//         <button
//           onClick={toggleFullscreen}
//           className="p-3 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
//           title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
//         >
//           {isFullscreen ? (
//             <Minimize2 className="w-5 h-5 text-gray-700" />
//           ) : (
//             <Maximize2 className="w-5 h-5 text-gray-700" />
//           )}
//         </button>
//       </div>

//       {/* Projects Counter */}
//       <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg px-4 py-2">
//         <div className="flex items-center gap-2">
//           <MapPin className="w-4 h-4 text-blue-600" />
//           <span className="text-sm font-semibold text-gray-700">
//             {projects.length} {projects.length === 1 ? 'Project' : 'Projects'}
//           </span>
//         </div>
//       </div>

//       {/* Selected Project Details Panel */}
//       {selectedProject && (
//         <div className="absolute bottom-4 left-4 right-4 md:left-4 md:right-auto md:w-96 z-[1000] bg-white rounded-xl shadow-2xl p-6 border border-gray-200">
//           <button
//             onClick={() => setSelectedProject(null)}
//             className="absolute top-3 right-3 p-1 hover:bg-gray-100 rounded-lg transition-colors"
//           >
//             <X className="w-5 h-5 text-gray-600" />
//           </button>

//           <h3 className="text-lg font-bold text-gray-900 mb-2 pr-8">
//             {selectedProject.name}
//           </h3>

//           {selectedProject.location && (
//             <p className="text-sm text-gray-600 mb-2 flex items-center gap-1">
//               <MapPin className="w-4 h-4" />
//               {selectedProject.location}
//             </p>
//           )}

//           {selectedProject.min_price && (
//             <div className="mb-4">
//               <p className="text-lg font-bold text-blue-600">
//                 {(selectedProject.min_price / 1000000).toFixed(1)}M EGP
//                 {selectedProject.max_price && (
//                   <span className="text-gray-500 font-normal text-sm">
//                     {' '}- {(selectedProject.max_price / 1000000).toFixed(1)}M
//                   </span>
//                 )}
//               </p>
//             </div>
//           )}

//           {selectedProject.description && (
//             <p className="text-sm text-gray-600 mb-4">
//               {selectedProject.description}
//             </p>
//           )}

//           <button
//             onClick={() => onProjectClick && onProjectClick(selectedProject)}
//             className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
//           >
//             View Full Details
//           </button>
//         </div>
//       )}
//     </div>
//   );
// }

// // Global click handler for popup buttons
// if (typeof window !== 'undefined') {
//   (window as any).handleProjectClick = (projectId: string) => {
//     console.log('Project clicked:', projectId);
//     // You can dispatch a custom event here or use a global state manager
//   };
// }

// export default ProjectsMap;


// components/ProjectsMap.tsx
"use client";

import React, { useEffect, useRef, useState } from 'react';
import { MapPin, X, Navigation, Maximize2, Minimize2, Search, Loader2, Map } from 'lucide-react';

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

interface ProjectsMapProps {
  projects?: Project[];
  center?: [number, number];
  zoom?: number;
  height?: string;
  onProjectClick?: (project: Project) => void;
}

const MAP_STYLES = {
  openstreetmap: {
    name: 'Street Map',
    tile: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap contributors',
  },
  satellite: {
    name: 'Satellite',
    tile: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '© Esri, DigitalGlobe, Earthstar Geographics',
  },
  dark: {
    name: 'Dark',
    tile: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '© CartoDB',
  },
  light: {
    name: 'Light',
    tile: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '© CartoDB',
  },
};

export function ProjectsMap({
  projects = [],
  center = [30.0444, 31.2357],
  zoom = 11,
  height = '600px',
  onProjectClick
}: ProjectsMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const searchMarkerRef = useRef<any>(null);
  const tileLayerRef = useRef<any>(null);
  
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [mapStyle, setMapStyle] = useState<keyof typeof MAP_STYLES>('openstreetmap');
  const [showStyleMenu, setShowStyleMenu] = useState(false);

  // Load Leaflet dynamically
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const loadLeaflet = async () => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);

      const L = await import('leaflet');
      
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });

      if (!mapRef.current || mapInstanceRef.current) return;

      const map = L.map(mapRef.current).setView(center, zoom);

      const style = MAP_STYLES[mapStyle];
      const tileLayer = L.tileLayer(style.tile, {
        attribution: style.attribution,
        maxZoom: 19,
      }).addTo(map);

      tileLayerRef.current = tileLayer;
      mapInstanceRef.current = map;

      const styleEl = document.createElement('style');
      styleEl.textContent = `
        .custom-marker {
          background-color: #2563eb;
          border: 3px solid white;
          border-radius: 50%;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
          cursor: pointer;
          transition: transform 0.2s;
        }
        .custom-marker:hover {
          transform: scale(1.2);
          background-color: #1d4ed8;
        }
        .custom-marker svg {
          width: 18px;
          height: 18px;
          color: white;
        }
        .search-marker {
          background-color: #ef4444;
          border: 3px solid white;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 0 8px rgba(239, 68, 68, 0.2);
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0.2); }
          50% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0.1); }
        }
      `;
      document.head.appendChild(styleEl);
    };

    loadLeaflet();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Change map style
  const changeMapStyle = (style: keyof typeof MAP_STYLES) => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;

    const L = require('leaflet');
    const newStyle = MAP_STYLES[style];

    mapInstanceRef.current.removeLayer(tileLayerRef.current);
    
    const newTileLayer = L.tileLayer(newStyle.tile, {
      attribution: newStyle.attribution,
      maxZoom: 19,
    }).addTo(mapInstanceRef.current);

    tileLayerRef.current = newTileLayer;
    setMapStyle(style);
    setShowStyleMenu(false);
  };

  // Add project markers
  useEffect(() => {
    if (!mapInstanceRef.current || !projects.length) return;

    const L = require('leaflet');

    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    projects.forEach((project) => {
      if (!project.latitude || !project.longitude) return;

      const customIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `
          <div class="custom-marker">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
      });

      const marker = L.marker([project.latitude, project.longitude], {
        icon: customIcon,
      }).addTo(mapInstanceRef.current);

      const popupContent = `
        <div style="min-width: 200px;">
          <h3 style="font-weight: bold; font-size: 16px; margin-bottom: 8px; color: #1e293b;">
            ${project.name}
          </h3>
          ${project.min_price ? `
            <p style="color: #2563eb; font-weight: 600; font-size: 14px; margin-bottom: 12px;">
              💰 ${(project.min_price / 1000000).toFixed(1)}M EGP
              ${project.max_price ? ` - ${(project.max_price / 1000000).toFixed(1)}M` : ''}
            </p>
          ` : ''}
          
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.on('click', () => {
        setSelectedProject(project);
        if (onProjectClick) {
          onProjectClick(project);
        }
      });

      markersRef.current.push(marker);
    });

    if (projects.length > 0) {
      const group = L.featureGroup(markersRef.current);
      mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
    }
  }, [projects, onProjectClick]);

  // Search for location using Nominatim (OpenStreetMap)
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    setShowSearchResults(false);

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?` +
        `q=${encodeURIComponent(searchQuery + ', Egypt')}` +
        `&format=json&limit=5&addressdetails=1`
      );

      const data = await response.json();
      
      if (data && data.length > 0) {
        setSearchResults(data);
        setShowSearchResults(true);
      } else {
        alert('Location not found. Try searching for: German University, Cairo University, New Cairo, etc.');
      }
    } catch (error) {
      console.error('Search error:', error);
      alert('Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  // Navigate to selected search result
  const selectSearchResult = (result: any) => {
    if (!mapInstanceRef.current) return;

    const L = require('leaflet');
    const lat = parseFloat(result.lat);
    const lon = parseFloat(result.lon);

    if (searchMarkerRef.current) {
      searchMarkerRef.current.remove();
    }

    const searchIcon = L.divIcon({
      className: 'search-location-marker',
      html: `
        <div class="search-marker">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="20" height="20">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2L12 22M2 12L22 12" stroke="white" stroke-width="2"/>
          </svg>
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });

    const marker = L.marker([lat, lon], { icon: searchIcon })
      .addTo(mapInstanceRef.current)
      .bindPopup(`
        <div style="text-align: center;">
          <strong>${result.display_name}</strong>
          <p style="margin-top: 8px; color: #64748b; font-size: 12px;">
            Nearby projects are shown in blue
          </p>
        </div>
      `)
      .openPopup();

    searchMarkerRef.current = marker;

    mapInstanceRef.current.setView([lat, lon], 14);

    setShowSearchResults(false);
    setSearchQuery(result.display_name.split(',')[0]);
  };

  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const userLoc: [number, number] = [
            position.coords.latitude,
            position.coords.longitude,
          ];
          setUserLocation(userLoc);

          if (mapInstanceRef.current) {
            const L = require('leaflet');
            
            const userIcon = L.divIcon({
              className: 'user-location-marker',
              html: `
                <div style="
                  background-color: #10b981;
                  border: 3px solid white;
                  border-radius: 50%;
                  width: 20px;
                  height: 20px;
                  box-shadow: 0 0 0 8px rgba(16, 185, 129, 0.2);
                "></div>
              `,
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            });

            L.marker(userLoc, { icon: userIcon })
              .addTo(mapInstanceRef.current)
              .bindPopup('📍 Your Location')
              .openPopup();

            mapInstanceRef.current.setView(userLoc, 13);
          }
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please enable location services.');
        }
      );
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className={`relative ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Search Bar */}
      <div className="absolute top-4 left-4 right-4 md:left-4 md:right-auto md:w-96 z-[1000]">
        <div className="bg-white rounded-lg shadow-lg p-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search location (e.g., German University)"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {searching ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Search className="w-5 h-5" />
              )}
            </button>
          </div>

          {/* Search Results Dropdown */}
          {showSearchResults && searchResults.length > 0 && (
            <div className="mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {searchResults.map((result, index) => (
                <button
                  key={index}
                  onClick={() => selectSearchResult(result)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors"
                >
                  <div className="flex items-start gap-2">
                    <MapPin className="w-4 h-4 text-blue-600 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {result.display_name.split(',')[0]}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {result.display_name}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Map Container */}
      <div
        ref={mapRef}
        style={{ height: isFullscreen ? '100vh' : height }}
        className="rounded-xl shadow-lg overflow-hidden border border-gray-200"
      />

      {/* Controls Overlay */}
      <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
        {/* Map Style Selector */}
        <div className="relative">
          <button
            onClick={() => setShowStyleMenu(!showStyleMenu)}
            className="p-3 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
            title="Change map style"
          >
            <Map className="w-5 h-5 text-gray-700" />
          </button>
          
          {showStyleMenu && (
            <div className="absolute top-12 right-0 bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
              {Object.entries(MAP_STYLES).map(([key, value]) => (
                <button
                  key={key}
                  onClick={() => changeMapStyle(key as keyof typeof MAP_STYLES)}
                  className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 transition-colors ${
                    mapStyle === key ? 'bg-blue-50 text-blue-600 font-semibold' : 'text-gray-700'
                  }`}
                >
                  {value.name}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={getUserLocation}
          className="p-3 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
          title="Get my location"
        >
          <Navigation className="w-5 h-5 text-gray-700" />
        </button>
        
        <button
          onClick={toggleFullscreen}
          className="p-3 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
          title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? (
            <Minimize2 className="w-5 h-5 text-gray-700" />
          ) : (
            <Maximize2 className="w-5 h-5 text-gray-700" />
          )}
        </button>
      </div>

      {/* Projects Counter */}
      <div className="absolute bottom-20 left-4 z-[1000] bg-white rounded-lg shadow-lg px-4 py-2">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-semibold text-gray-700">
            {projects.length} {projects.length === 1 ? 'Project' : 'Projects'}
          </span>
        </div>
      </div>

      {/* Selected Project Details Panel - Minimal */}
      
    </div>
  );
}

if (typeof window !== 'undefined') {
  (window as any).handleProjectClick = (projectId: string) => {
    console.log('Project clicked:', projectId);
  };
}

export default ProjectsMap;