// // components/auth/AuthContext.tsx
// "use client";

// import React, { createContext, useContext, useState, useEffect } from "react";

// interface User {
//   id: string;
//   email: string;
//   name: string;
//   createdAt: string;
// }

// interface AuthContextType {
//   user: User | null;
//   loading: boolean;
//   login: (email: string, password: string) => Promise<void>;
//   register: (email: string, password: string, name: string) => Promise<void>;
//   logout: () => Promise<void>;
//   isAuthenticated: boolean;
// }

// const AuthContext = createContext<AuthContextType | undefined>(undefined);

// export const useAuth = () => {
//   const context = useContext(AuthContext);
//   if (!context) {
//     throw new Error("useAuth must be used within an AuthProvider");
//   }
//   return context;
// };

// export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
//   children,
// }) => {
//   const [user, setUser] = useState<User | null>(null);
//   const [loading, setLoading] = useState(true);

//   // Check if user is logged in on mount
//   useEffect(() => {
//     checkAuth();
//   }, []);

//   const checkAuth = async () => {
//     try {
//       const token = localStorage.getItem("authToken");
//       if (!token) {
//         setLoading(false);
//         return;
//       }

//       const response = await fetch("http://localhost:8000/api/auth/me", {
//         headers: {
//           Authorization: `Bearer ${token}`,
//         },
//       });

//       if (response.ok) {
//         const userData = await response.json();
//         setUser(userData);
//       } else {
//         localStorage.removeItem("authToken");
//       }
//     } catch (error) {
//       console.error("Auth check failed:", error);
//       localStorage.removeItem("authToken");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const login = async (email: string, password: string) => {
//     try {
//       const response = await fetch("http://localhost:8000/api/auth/login", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ email, password }),
//       });

//       if (!response.ok) {
//         const error = await response.json();
//         throw new Error(error.message || "Login failed");
//       }

//       const data = await response.json();
//       localStorage.setItem("authToken", data.token);
//       setUser(data.user);
//     } catch (error) {
//       throw error;
//     }
//   };

//   const register = async (email: string, password: string, name: string) => {
//     try {
//       const response = await fetch("http://localhost:8000/api/auth/register", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({ email, password, name }),
//       });

//       if (!response.ok) {
//         const error = await response.json();
//         throw new Error(error.message || "Registration failed");
//       }

//       const data = await response.json();
//       localStorage.setItem("authToken", data.token);
//       setUser(data.user);
//     } catch (error) {
//       throw error;
//     }
//   };

//   const logout = async () => {
//     try {
//       const token = localStorage.getItem("authToken");
//       if (token) {
//         await fetch("http://localhost:8000/api/auth/logout", {
//           method: "POST",
//           headers: {
//             Authorization: `Bearer ${token}`,
//           },
//         });
//       }
//     } catch (error) {
//       console.error("Logout error:", error);
//     } finally {
//       localStorage.removeItem("authToken");
//       setUser(null);
//     }
//   };

//   const value = {
//     user,
//     loading,
//     login,
//     register,
//     logout,
//     isAuthenticated: !!user,
//   };

//   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// };

//components/auth/AuthContext.tsx
"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
  thread_id?: string; // Add this to see the thread_id
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem("authToken");
      console.log("🔍 Checking auth, token exists:", !!token);
      
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch("http://localhost:8000/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      console.log("📥 Response status:", response.status);

      if (response.ok) {
        const userData = await response.json();
        console.log("✅ User authenticated:", userData);
        setUser(userData);
      } else {
        console.log("❌ Token invalid, removing from storage");
        localStorage.removeItem("authToken");
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      localStorage.removeItem("authToken");
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Login failed");
      }

      const data = await response.json();
      console.log("✅ Login response:", data);
      
      // ✅ FIX: Use data.access_token instead of data.token
      localStorage.setItem("authToken", data.access_token);
      setUser(data.user);
      
      console.log("🔐 Token saved to localStorage");
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const response = await fetch("http://localhost:8000/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, name }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Registration failed");
      }

      const data = await response.json();
      console.log("✅ Register response:", data);
      
      // ✅ FIX: Use data.access_token instead of data.token
      localStorage.setItem("authToken", data.access_token);
      setUser(data.user);
      
      console.log("🔐 Token saved to localStorage");
    } catch (error) {
      console.error("Register error:", error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem("authToken");
      if (token) {
        await fetch("http://localhost:8000/api/auth/logout", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("authToken");
      setUser(null);
      console.log("✅ User logged out");
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

