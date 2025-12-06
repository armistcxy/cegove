// src/context/UserContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { getUserProfile } from '../pages/User/Utils/ApiFunction';
import {logout} from "../pages/Auth/Utils/ApiFunction.ts";

interface UserContextType {
    isLoggedIn: boolean;
    userProfile: any;
    isLoading: boolean;
    setUserProfile: (user: any) => void;
    setIsLoggedIn: (status: boolean) => void;
    refreshUserProfile: () => Promise<void>;
    handleLogout: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [userProfile, setUserProfile] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshUserProfile = async () => {
        const token = localStorage.getItem("access-token");
        setIsLoading(true);
        if (token) {
            try {
                const response = await getUserProfile(token);
                setIsLoggedIn(true);
                setUserProfile(response.data);
            } catch (error) {
                console.error("Error fetching user profile:", error);
                setIsLoggedIn(false);
                setUserProfile(null);
            }
        }
        setIsLoading(false);
    };

    const handleLogout = () => {
        logout(localStorage.getItem("access-token") || "");
        localStorage.removeItem("access-token");
        setIsLoggedIn(false);
        setUserProfile(null);
    };

    useEffect(() => {
        refreshUserProfile();
    }, []);

    return (
        <UserContext.Provider value={{
            isLoggedIn,
            userProfile,
            isLoading,
            setUserProfile,
            setIsLoggedIn,
            refreshUserProfile,
            handleLogout
        }}>
            {children}
        </UserContext.Provider>
    );
};

export const useUser = () => {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUser must be used within UserProvider');
    }
    return context;
};