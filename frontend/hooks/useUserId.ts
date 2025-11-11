'use client';

import { useState, useEffect } from 'react';

export const useUserId = () => {
    const [userId, setUserId] = useState<string | null>(null);
    const [isAuthReady, setIsAuthReady] = useState<boolean>(false);

    useEffect(() => {
        if (typeof window === 'undefined') return;

        // Genera o recupera un ID utente da localStorage
        let storedUserId = localStorage.getItem('ragUserId');
        if (!storedUserId) {
            storedUserId = 'user_' + Math.random().toString(36).substring(2, 15);
            localStorage.setItem('ragUserId', storedUserId);
        }
        setUserId(storedUserId);
        setIsAuthReady(true);
    }, []);

    return { userId, isAuthReady };
};
