interface SettingsViewProps {
  onDeleteAccount: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onDeleteAccount }) => {
  return (
    <div className="p-4">
      <div className="border-2 border-indigo-300 dark:border-indigo-700 rounded-lg p-4">
        <h3 className="text-base font-semibold text-indigo-900 dark:text-indigo-50 mb-2">
          Account Management
        </h3>
        <p className="text-sm text-indigo-700 dark:text-indigo-200 mb-4">
          Permanently delete your account and all associated data. This action cannot be undone.
        </p>
        <button
          onClick={onDeleteAccount}
          className="min-h-[44px] w-full px-4 py-2 text-sm font-medium text-red-700 dark:text-red-400 border-2 border-red-300 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors focus:outline-none focus:ring-3 focus:ring-focus"
        >
          Delete Account
        </button>
      </div>
    </div>
  );
};
