import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  icon?: string;
  badge?: number | string;
  count?: number | string;
  badgeColor?: string;
}

interface ContextTabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange?: (tabId: string) => void;
  onTabChange?: (tabId: string) => void;
  className?: string;
}

export const ContextTabs: React.FC<ContextTabsProps> = ({
  tabs,
  activeTab,
  onChange,
  onTabChange,
  className = '',
}) => {
  const handleChange = (tabId: string) => {
    if (onTabChange) onTabChange(tabId);
    if (onChange) onChange(tabId);
  };
  return (
    <div className={`border-b border-slate-800 bg-slate-950/70 backdrop-blur-sm px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-2">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleChange(tab.id)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-150 flex items-center gap-2 cursor-pointer ${
                isActive
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-[0_0_12px_rgba(245,158,11,0.08)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              {tab.icon && (
                <i
                  className={`${tab.icon} text-xs ${
                    isActive ? 'text-amber-400' : 'text-slate-500'
                  }`}
                />
              )}
              <span>{tab.label}</span>
              {(tab.badge !== undefined && tab.badge !== null) ? (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    tab.badgeColor || (isActive ? 'bg-amber-500/25 text-amber-200' : 'bg-slate-800 text-slate-400')
                  }`}
                >
                  {tab.badge}
                </span>
              ) : (tab.count !== undefined && tab.count !== null) ? (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    isActive ? 'bg-amber-500/25 text-amber-200' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {tab.count}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
};
