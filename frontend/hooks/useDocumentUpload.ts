'use client';

import { useState, useCallback } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import type { AlertState } from '@/lib/types';
import { API_BASE_URL } from '@/lib/constants';

interface UseUploadResult {
    file: File | null;
    setFile: React.Dispatch<React.SetStateAction<File | null>>;
    isUploading: boolean;
    uploadAlert: AlertState;
    handleFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
    handleUpload: (e: FormEvent, currentUserId: string) => Promise<void>;
}

export const useDocumentUpload = (): UseUploadResult => {
    const [file, setFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [uploadAlert, setUploadAlert] = useState<AlertState>({
        message: "Inserisci un ID Utente e carica un PDF.",
        type: 'info'
    });

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            if (selectedFile.type !== "application/pdf") {
                setUploadAlert({ message: "Solo i file PDF sono supportati.", type: 'error' });
                setFile(null);
            } else {
                setFile(selectedFile);
                setUploadAlert({ message: selectedFile.name + " pronto per l'indicizzazione.", type: 'info' });
            }
        } else {
            setFile(null);
            setUploadAlert({ message: "Nessun file selezionato.", type: 'info' });
        }
    };

    const handleUpload = useCallback(async (e: FormEvent, currentUserId: string) => {
        e.preventDefault();
        if (!file || !currentUserId) {
            setUploadAlert({
                message: "Seleziona un file PDF e assicurati che l'ID Utente sia disponibile.",
                type: 'error'
            });
            return;
        }

        setIsUploading(true);
        setUploadAlert({ message: 'Caricamento e indicizzazione in corso...', type: 'info' });

        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', currentUserId);

        try {
            const response = await fetch(`${API_BASE_URL}/upload/`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                setUploadAlert({
                    message: `${data.message} Chunks indicizzati: ${data.chunks_indexed}. Ora puoi chattare!`,
                    type: 'success'
                });
                setFile(null);
                const fileInput = document.getElementById('pdf-upload') as HTMLInputElement;
                if (fileInput) fileInput.value = '';

            } else {
                setUploadAlert({
                    message: `Errore durante l'upload: ${data.detail || 'Errore sconosciuto'}`,
                    type: 'error'
                });
            }
        } catch (error) {
            console.error('Upload Error:', error);
            setUploadAlert({ message: `Errore di rete: Impossibile connettersi al backend.`, type: 'error' });
        } finally {
            setIsUploading(false);
        }
    }, [file]);

    return { file, setFile, isUploading, uploadAlert, handleFileChange, handleUpload };
};
