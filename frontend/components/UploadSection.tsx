import { FormEvent, ChangeEvent } from 'react';
import { Upload, Loader } from 'lucide-react';
import type { AlertState } from '@/lib/types';
import { AlertMessage } from './AlertMessage';

interface UploadSectionProps {
    file: File | null;
    isUploading: boolean;
    userId: string | null;
    uploadAlert: AlertState;
    statusAlert: AlertState | null;
    onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
    onUpload: (e: FormEvent) => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({
    file,
    isUploading,
    userId,
    uploadAlert,
    statusAlert,
    onFileChange,
    onUpload
}) => {
    return (
        <>
            <section>
                <h2 className="text-lg font-bold text-gray-800 dark:text-white mb-3 flex items-center border-b border-gray-100 dark:border-gray-700 pb-2">
                    <Upload size={16} className="mr-2 text-blue-600" /> 1. Indicizzazione Documenti
                </h2>
                <form onSubmit={onUpload} className="space-y-4">
                    <label htmlFor="pdf-upload" className="block text-xs font-bold text-gray-700 dark:text-gray-300 uppercase mb-1">
                        Carica Documento PDF
                    </label>

                    <div className="relative border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 hover:border-blue-400 dark:hover:border-blue-500 transition duration-300 cursor-pointer">
                        <input
                            type="file"
                            id="pdf-upload"
                            accept=".pdf"
                            onChange={onFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <div className="text-center">
                            <Upload size={24} className="mx-auto text-blue-500" />
                            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                                {file ? (
                                    <span className="font-semibold text-blue-600 truncate block">
                                        {file.name}
                                    </span>
                                ) : (
                                    "Trascina o clicca qui per selezionare un file (solo PDF)"
                                )}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">Max 1MB per demo.</p>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isUploading || !file || !userId}
                        className={`w-full flex justify-center items-center py-3 px-4 text-sm font-bold rounded-lg shadow-lg transition duration-200 transform hover:scale-[1.01] ${isUploading || !file || !userId
                                ? 'bg-gray-300 text-gray-600 cursor-not-allowed dark:bg-gray-600 dark:text-gray-300'
                                : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-xl'
                            }`}
                    >
                        {isUploading ? (
                            <>
                                <Loader size={18} className="animate-spin mr-2" />
                                Indicizzazione in corso...
                            </>
                        ) : (
                            <>
                                <Upload size={18} className="mr-2" />
                                Avvia Indicizzazione RAG
                            </>
                        )}
                    </button>
                </form>
            </section>

            <AlertMessage alert={uploadAlert} />
            {statusAlert && <AlertMessage alert={statusAlert} />}
        </>
    );
};
