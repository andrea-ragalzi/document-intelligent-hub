import type { ChatMessage } from '@/lib/types';
import { MessageSquare, User as UserIcon, Loader } from 'lucide-react';

interface ChatMessageDisplayProps {
    msg: ChatMessage;
}

export const ChatMessageDisplay: React.FC<ChatMessageDisplayProps> = ({ msg }) => {
    const isUser = msg.type === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
            <div className={`max-w-[85%] p-4 rounded-3xl shadow-lg transition duration-300 ${isUser
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-white text-gray-800 rounded-tl-none border border-gray-100 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600'
                }`}>
                <div className={`flex items-center mb-2 font-semibold text-xs uppercase ${isUser ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                    {isUser ? (
                        <UserIcon size={12} className="mr-2" />
                    ) : (
                        <MessageSquare size={12} className="mr-2 text-blue-600" />
                    )}
                    {isUser ? 'Tu' : 'Assistente'}
                </div>

                {msg.isThinking ? (
                    <div className="flex items-center text-sm text-blue-500 dark:text-blue-300">
                        <Loader size={16} className="animate-spin mr-2" />
                        <span className="italic">{msg.text}</span>
                    </div>
                ) : (
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
                )}

                {!isUser && msg.sources.length > 0 && !msg.isThinking && (
                    <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-600">
                        <span className="text-xs font-bold text-blue-600 dark:text-blue-400 block mb-1">
                            Fonti trovate ({msg.sources.length}):
                        </span>
                        <ul className="list-disc list-inside text-xs text-gray-600 dark:text-gray-300 space-y-0.5 max-h-24 overflow-y-auto pr-2">
                            {msg.sources.map((source, i) => (
                                <li key={i} className="truncate" title={source}>
                                    {source}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
};
