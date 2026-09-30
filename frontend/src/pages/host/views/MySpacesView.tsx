import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Space } from '../../../types';
import { getHostSpaces, publishSpace, unpublishSpace } from '../../../services/host';
import {
  HostPageHeader,
  HostCardSkeleton,
  HostTableSkeleton,
  HostEmptyState,
  StatusBadge,
} from '../components';

export const MySpacesView: React.FC = () => {
  const navigate = useNavigate();

  const [spaces, setSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterTab, setFilterTab] = useState<'all' | 'published' | 'draft' | 'pending'>('all');
  const [viewMode, setViewMode] = useState<'card' | 'table'>('card');
  const [searchQuery, setSearchQuery] = useState('');
  const [togglingId, setTogglingId] = useState<number | null>(null);

  useEffect(() => {
    loadSpaces();
  }, []);

  const loadSpaces = async () => {
    try {
      setLoading(true);
      const res = await getHostSpaces();
      if (res && res.spaces) {
        setSpaces(res.spaces);
      }
    } catch (err) {
      console.error('Failed to load host spaces:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (e: React.MouseEvent, space: Space) => {
    e.stopPropagation();
    try {
      setTogglingId(space.id);
      if (space.is_active) {
        await unpublishSpace(space.id);
        setSpaces(prev =>
          prev.map(s => (s.id === space.id ? { ...s, is_active: false, status: 'unavailable' } : s))
        );
      } else {
        await publishSpace(space.id);
        setSpaces(prev =>
          prev.map(s => (s.id === space.id ? { ...s, is_active: true, status: 'published' } : s))
        );
      }
    } catch (err) {
      console.error('Failed to toggle space status:', err);
    } finally {
      setTogglingId(null);
    }
  };

  // Filter logic
  const filteredSpaces = spaces.filter(space => {
    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = space.title.toLowerCase().includes(q);
      const matchCat = (space.category || '').toLowerCase().includes(q);
      const matchLoc = (space.location || space.address || '').toLowerCase().includes(q);
      if (!matchTitle && !matchCat && !matchLoc) return false;
    }

    // Status filter
    if (filterTab === 'published') return space.is_active;
    if (filterTab === 'draft') return !space.is_active;
    if (filterTab === 'pending') return !space.is_verified;
    return true;
  });

  const counts = {
    all: spaces.length,
    published: spaces.filter(s => s.is_active).length,
    draft: spaces.filter(s => !s.is_active).length,
    pending: spaces.filter(s => !s.is_verified).length,
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Physical Space Fleet"
        title="My Physical Spaces"
        subtitle="Manage your registered listings, pricing models, physical access keys, and Discom verification."
        actions={
          <button
            onClick={() => navigate('/host/spaces/create')}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition flex items-center justify-center gap-2"
          >
            <i className="fa-solid fa-plus text-xs" />
            <span>List New Space</span>
          </button>
        }
      />

      {/* Control Bar: Filters, Search, View Mode */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-3 rounded-2xl">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {[
            { id: 'all', label: 'All Spaces', count: counts.all },
            { id: 'published', label: 'Published', count: counts.published },
            { id: 'draft', label: 'Draft / Inactive', count: counts.draft },
            { id: 'pending', label: 'Pending Verification', count: counts.pending },
          ].map(tab => {
            const active = filterTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setFilterTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-1.5 ${
                  active
                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <span>{tab.label}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                    active ? 'bg-amber-500/25 text-amber-200' : 'bg-slate-800 text-slate-500'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search & View Mode */}
        <div className="flex items-center gap-2.5">
          <div className="relative flex-1 md:w-64">
            <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search space title, address..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none transition"
            />
          </div>

          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-0.5">
            <button
              onClick={() => setViewMode('card')}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === 'card' ? 'bg-slate-800 text-amber-400' : 'text-slate-500 hover:text-slate-300'
              }`}
              title="Card View"
            >
              <i className="fa-solid fa-grip" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-lg text-xs transition ${
                viewMode === 'table' ? 'bg-slate-800 text-amber-400' : 'text-slate-500 hover:text-slate-300'
              }`}
              title="Table View"
            >
              <i className="fa-solid fa-list" />
            </button>
          </div>
        </div>
      </div>

      {/* Spaces Listing */}
      {loading ? (
        viewMode === 'card' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <HostCardSkeleton lines={4} />
            <HostCardSkeleton lines={4} />
            <HostCardSkeleton lines={4} />
          </div>
        ) : (
          <HostTableSkeleton rows={5} cols={6} />
        )
      ) : filteredSpaces.length === 0 ? (
        <HostEmptyState
          icon="fa-solid fa-building-circle-exclamation"
          title="No Spaces Found"
          description={
            searchQuery
              ? 'No spaces matched your current search filters. Try clearing your query.'
              : 'You have not registered any spaces matching this category yet.'
          }
          primaryAction={{
            label: 'List New Space',
            onClick: () => navigate('/host/spaces/create'),
            icon: 'fa-solid fa-plus',
          }}
          secondaryAction={
            searchQuery
              ? {
                  label: 'Clear Search',
                  onClick: () => setSearchQuery(''),
                }
              : undefined
          }
        />
      ) : viewMode === 'card' ? (
        /* Card Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredSpaces.map(space => {
            const isLive = space.active_session;
            return (
              <div
                key={space.id}
                onClick={() => navigate(`/host/spaces/${space.id}`)}
                className={`bg-slate-900/70 border rounded-2xl overflow-hidden cursor-pointer group transition-all duration-200 hover:shadow-xl hover:shadow-amber-500/5 ${
                  isLive
                    ? 'border-emerald-500/50 ring-1 ring-emerald-500/30'
                    : 'border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/90'
                }`}
              >
                {/* Image & Header Tags */}
                <div className="h-44 relative bg-slate-950 overflow-hidden">
                  <img
                    src={space.image_url || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'}
                    alt={space.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent" />

                  {/* Status Badges on Image */}
                  <div className="absolute top-3 left-3 flex items-center gap-1.5 flex-wrap">
                    <StatusBadge status={space.is_active ? 'published' : 'draft'} type="space" />
                    {space.is_verified ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 backdrop-blur-sm flex items-center gap-1">
                        <i className="fa-solid fa-shield-check text-[9px]" />
                        <span>Discom Verified</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 backdrop-blur-sm flex items-center gap-1">
                        <i className="fa-solid fa-clock text-[9px]" />
                        <span>Unverified</span>
                      </span>
                    )}
                  </div>

                  {/* Live Beacon */}
                  {isLive && (
                    <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500 text-slate-950 flex items-center gap-1.5 shadow-lg animate-pulse">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-950" />
                      <span>LIVE OCCUPIED</span>
                    </div>
                  )}

                  {/* Rate Chip */}
                  <div className="absolute bottom-3 left-3">
                    <span className="text-lg font-black text-white font-mono">₹{space.hourly_rate}</span>
                    <span className="text-[11px] text-slate-300">/hr</span>
                  </div>

                  {/* Access Tag */}
                  <div className="absolute bottom-3 right-3 text-[10px] font-mono text-slate-300 bg-slate-950/80 px-2 py-0.5 rounded-md border border-slate-800">
                    <i className="fa-solid fa-key text-amber-400 mr-1" />
                    {space.physical_access_type || 'room_qr'}
                  </div>
                </div>

                {/* Content */}
                <div className="p-4 space-y-3">
                  <div>
                    <h3 className="font-bold text-white text-sm group-hover:text-amber-400 transition truncate">
                      {space.title}
                    </h3>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      <i className="fa-solid fa-location-dot text-slate-500 mr-1 text-[10px]" />
                      {space.location || space.address || 'Address provided on booking'}
                    </p>
                  </div>

                  {/* Metrics Bar */}
                  <div className="grid grid-cols-3 gap-2 py-2 px-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
                    <div>
                      <div className="text-[10px] text-slate-500">Bookings</div>
                      <div className="text-xs font-bold text-slate-200 font-mono">{space.bookings_count || 0}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">Upcoming</div>
                      <div className="text-xs font-bold text-amber-400 font-mono">{space.upcoming_count || 0}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">Revenue</div>
                      <div className="text-xs font-bold text-emerald-400 font-mono">₹{space.total_revenue || 0}</div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
                    <button
                      onClick={(e) => handleToggleActive(e, space)}
                      disabled={togglingId === space.id}
                      className={`text-xs font-semibold px-2.5 py-1.5 rounded-xl border transition ${
                        space.is_active
                          ? 'border-slate-700 text-slate-400 hover:text-rose-400 hover:border-rose-500/40'
                          : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                      }`}
                    >
                      {togglingId === space.id ? (
                        <i className="fa-solid fa-spinner animate-spin text-xs" />
                      ) : space.is_active ? (
                        'Deactivate'
                      ) : (
                        'Publish'
                      )}
                    </button>

                    <div className="flex items-center gap-1.5">
                      {isLive && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/host/live-sessions`);
                          }}
                          className="px-2.5 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold hover:bg-emerald-500/30 transition"
                        >
                          Cockpit
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/host/spaces/${space.id}`);
                        }}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
                      >
                        Manage →
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Space</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Pricing</th>
                  <th className="p-3.5">Access Type</th>
                  <th className="p-3.5">Bookings</th>
                  <th className="p-3.5">Revenue</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredSpaces.map(space => (
                  <tr
                    key={space.id}
                    onClick={() => navigate(`/host/spaces/${space.id}`)}
                    className="hover:bg-slate-800/40 cursor-pointer transition group"
                  >
                    <td className="p-3.5">
                      <div className="flex items-center gap-3">
                        <img
                          src={space.image_url || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=150&q=80'}
                          alt={space.title}
                          className="w-10 h-10 rounded-xl object-cover border border-slate-800"
                        />
                        <div>
                          <div className="font-bold text-white group-hover:text-amber-400 transition">
                            {space.title}
                          </div>
                          <div className="text-[11px] text-slate-400">{space.category} • {space.location || 'Bangalore'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <div className="flex items-center gap-1.5">
                        <StatusBadge status={space.is_active ? 'published' : 'draft'} type="space" />
                        {space.is_verified && (
                          <span className="w-2 h-2 rounded-full bg-emerald-400" title="Discom Verified" />
                        )}
                      </div>
                    </td>
                    <td className="p-3.5 font-bold text-white font-mono">
                      ₹{space.hourly_rate}/hr
                    </td>
                    <td className="p-3.5 font-mono text-[11px] text-slate-300">
                      {space.physical_access_type || 'room_qr'}
                    </td>
                    <td className="p-3.5 text-slate-300 font-mono">
                      {space.bookings_count || 0}
                    </td>
                    <td className="p-3.5 font-bold text-emerald-400 font-mono">
                      ₹{space.total_revenue || 0}
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/host/spaces/${space.id}`);
                        }}
                        className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                      >
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
