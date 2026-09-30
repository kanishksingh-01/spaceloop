import React, { useState, useEffect } from 'react';
import { Space } from '../../../types';
import { getHostSpaces, editSpace, getHostActivity } from '../../../services/host';

export const AccessSecurityView: React.FC = () => {
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [accessLogs, setAccessLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingSpaceId, setSavingSpaceId] = useState<number | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sRes, aRes] = await Promise.all([
        getHostSpaces(),
        getHostActivity('access'),
      ]);
      if (sRes && sRes.spaces) setSpaces(sRes.spaces);
      if (aRes && aRes.events) setAccessLogs(aRes.events);
    } catch (err) {
      console.error('Failed to load access & security data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAccess = async (space: Space, accessType: string, keyboxCode?: string, radius?: number) => {
    try {
      setSavingSpaceId(space.id);
      await editSpace(space.id, {
        physical_access_type: accessType,
        keybox_code: keyboxCode !== undefined ? keyboxCode : space.keybox_code,
        geofence_radius_meters: radius !== undefined ? radius : space.geofence_radius_meters,
      });

      setSpaces(prev =>
        prev.map(s =>
          s.id === space.id
            ? {
                ...s,
                physical_access_type: accessType,
                keybox_code: keyboxCode !== undefined ? keyboxCode : s.keybox_code,
                geofence_radius_meters: radius !== undefined ? radius : s.geofence_radius_meters,
              }
            : s
        )
      );

      setSuccessMsg(`Access parameters updated for "${space.title}".`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Failed to update access:', err);
    } finally {
      setSavingSpaceId(null);
    }
  };

  const handleRegenerateQrToken = async (space: Space) => {
    const newToken = `SL-ROOM-${space.id}-${Math.floor(100000 + Math.random() * 900000)}`;
    try {
      setSavingSpaceId(space.id);
      await editSpace(space.id, { room_qr_token: newToken });
      setSpaces(prev =>
        prev.map(s => (s.id === space.id ? { ...s, room_qr_token: newToken } : s))
      );
      setSuccessMsg(`Generated new room QR token for "${space.title}".`);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Failed to regenerate QR token:', err);
    } finally {
      setSavingSpaceId(null);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Physical Access & Security
          </span>
          <span className="text-slate-500 text-xs font-mono">Haversine GPS Perimeter • Dynamic Credentialing</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Access Control Console
        </h1>
        <p className="text-slate-400 text-xs md:text-sm mt-0.5">
          Configure physical door unlocks, 50-meter arrival geofences, and inspect entry attempt telemetry.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
          <i className="fa-solid fa-circle-check text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Space Access Configurations */}
      <div className="space-y-4">
        <h2 className="text-base font-bold text-white">Space Physical Doors & Perimeter Rules</h2>

        {loading ? (
          <div className="py-16 text-center text-slate-400 text-xs font-mono">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            LOADING PHYSICAL ACCESS CONTROLS...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {spaces.map(space => {
              const currentType = space.physical_access_type || 'room_qr';
              const radius = space.geofence_radius_meters || 50;
              const qrToken = space.room_qr_token || `SL-ROOM-${space.id}-4819`;
              const isSaving = savingSpaceId === space.id;

              return (
                <div
                  key={space.id}
                  className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-white text-sm truncate">{space.title}</h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                      ID #{space.id}
                    </span>
                  </div>

                  <div className="space-y-3 text-xs">
                    <div>
                      <label className="text-slate-400 block mb-1">Access Method</label>
                      <select
                        value={currentType}
                        onChange={e => handleUpdateAccess(space, e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white"
                      >
                        <option value="room_qr">Room Dynamic QR Code</option>
                        <option value="keybox">Keybox / Lockbox PIN</option>
                        <option value="smart_lock">Smart Door Lock (BLE / WiFi)</option>
                        <option value="host_greeter">In-Person Host Greeting</option>
                      </select>
                    </div>

                    {currentType === 'room_qr' && (
                      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 text-[11px]">Room QR Token:</span>
                          <button
                            type="button"
                            onClick={() => handleRegenerateQrToken(space)}
                            disabled={isSaving}
                            className="text-[10px] text-amber-400 hover:text-amber-300 font-semibold"
                          >
                            Regenerate
                          </button>
                        </div>
                        <div className="font-mono text-xs text-amber-300 bg-slate-900 px-2 py-1 rounded border border-slate-800 select-all">
                          {qrToken}
                        </div>
                      </div>
                    )}

                    {currentType === 'keybox' && (
                      <div>
                        <label className="text-slate-400 block mb-1">Keybox Lock PIN</label>
                        <input
                          type="text"
                          defaultValue={space.keybox_code || '4819'}
                          onBlur={e => handleUpdateAccess(space, currentType, e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white font-mono"
                        />
                      </div>
                    )}

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-slate-400">Arrival Perimeter</label>
                        <span className="font-mono text-amber-400 font-bold">{radius}m</span>
                      </div>
                      <input
                        type="range"
                        min={20}
                        max={150}
                        step={5}
                        defaultValue={radius}
                        onChange={e => handleUpdateAccess(space, currentType, undefined, Number(e.target.value))}
                        className="w-full accent-amber-500 cursor-pointer"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Access Attempts & Telemetry Audit Log */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-base font-bold text-white">Physical Access Attempt History</h3>
        {accessLogs.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs">
            No access handshake attempts recorded in the audit log yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {accessLogs.map((log, idx) => (
              <div key={idx} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center text-xs">
                    <i className="fa-solid fa-key" />
                  </div>
                  <div>
                    <div className="font-semibold text-white">{log.title || 'Access Handshake Granted'}</div>
                    <div className="text-[11px] text-slate-400">
                      {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {log.description}
                    </div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  50m Verified
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
