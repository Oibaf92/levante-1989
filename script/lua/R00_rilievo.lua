--[[
  LEVANTE 1989 - R00 "Rilievo del terreno"

  Campiona il terreno di DCS su una o piu' griglie regolari e scrive un file di
  testo in  Saved Games\DCS\Levante1989\rilievo_terreno.txt

  Per ogni punto:  quota (m), pendenza (%), tipo di superficie, numero di
  edifici entro RAGGIO_EDIFICI, distanza dalla strada piu' vicina (m).
  Gli alberi NON sono rilevabili dagli script di DCS.

  Parametri in LEVANTE_RILIEVO = { regioni = { {nome, x0, y0, passo, nx, ny}, ... } }
  (coordinate della mappa DCS: x = nord, y = est).

  Formato del file:
    # commenti
    R,<nome>,<x0>,<y0>,<passo>,<nx>,<ny>      inizio di una regione
    <i>,<quota>,<pendenza>,<sup>,<edifici>,<strada>;<quota>,...   una riga per ogni i (nord),
                                                                   un gruppo per ogni j (est)
    sup: 1 terra, 2 acqua bassa, 3 acqua, 4 strada, 5 pista; acqua -> solo "3"
    FINE                                                  rilievo completato
]]

local P = LEVANTE_RILIEVO or {}
local REGIONI = P.regioni or {}
local RAGGIO_EDIFICI = P.raggio_edifici or 400
local DELTA_PENDENZA = 150          -- m: distanza per il calcolo della pendenza
local STRADA_MAX = 20000            -- m: oltre questa distanza si scrive 20000
local PUNTI_PER_PASSO = P.punti_per_passo or 400

local function log(msg) env.info("[LEVANTE R00] " .. msg) end
local function messaggio(msg, durata) trigger.action.outText(msg, durata or 10, true) end

if not (io and lfs) then
  messaggio("RILIEVO IMPOSSIBILE: MissionScripting.lua non e' stato modificato (io/lfs bloccati).", 120)
  return
end

local cartella = lfs.writedir() .. "Levante1989\\"
lfs.mkdir(cartella)
local percorso = cartella .. "rilievo_terreno.txt"
local f = io.open(percorso, "w")
if not f then
  messaggio("RILIEVO IMPOSSIBILE: non riesco a scrivere " .. percorso, 120)
  return
end

local totale = 0
for _, r in ipairs(REGIONI) do totale = totale + r.nx * r.ny end
f:write("# Levante 1989 - rilievo del terreno di DCS\n")
f:write(string.format("# teatro %s, punti totali %d, raggio edifici %d m, delta pendenza %d m\n",
  env.mission.theatre or "?", totale, RAGGIO_EDIFICI, DELTA_PENDENZA))

------------------------------------------------------------------------
local function contaEdifici(x, h, z)
  local n = 0
  local vol = { id = world.VolumeType.SPHERE, params = { point = { x = x, y = h, z = z }, radius = RAGGIO_EDIFICI } }
  world.searchObjects(Object.Category.SCENERY, vol, function() n = n + 1; return n < 99 end)
  return n
end

local function distanzaStrada(x, z)
  local ok, rx, rz = pcall(land.getClosestPointOnRoads, "roads", x, z)
  if not ok or not rx then return -1 end
  local d = math.sqrt((rx - x) ^ 2 + (rz - z) ^ 2)
  if d > STRADA_MAX then d = STRADA_MAX end
  return math.floor(d / 10 + 0.5) * 10
end

local function misura(x, z)
  local sup = land.getSurfaceType({ x = x, y = z })
  if sup == land.SurfaceType.WATER then return "3" end
  local h = land.getHeight({ x = x, y = z })
  local d = DELTA_PENDENZA
  local hn = land.getHeight({ x = x + d, y = z })
  local hs = land.getHeight({ x = x - d, y = z })
  local he = land.getHeight({ x = x, y = z + d })
  local ho = land.getHeight({ x = x, y = z - d })
  local gx = (hn - hs) / (2 * d)
  local gz = (he - ho) / (2 * d)
  local pend = math.floor(math.sqrt(gx * gx + gz * gz) * 100 + 0.5)
  return string.format("%d,%d,%d,%d,%d", math.floor(h + 0.5), pend, sup, contaEdifici(x, h, z), distanzaStrada(x, z))
end

------------------------------------------------------------------------
local stato = { regione = 1, i = 0, fatti = 0, ultimaPercentuale = -5, riga = {} }

local function iniziaRegione(r)
  f:write(string.format("R,%s,%.1f,%.1f,%d,%d,%d\n", r.nome, r.x0, r.y0, r.passo, r.nx, r.ny))
  log(string.format("regione %s: %d x %d punti, passo %d m", r.nome, r.nx, r.ny, r.passo))
end

local function passo()
  local r = REGIONI[stato.regione]
  if not r then
    f:write("FINE\n")
    f:close()
    messaggio("RILIEVO COMPLETATO.\nFile: " .. percorso .. "\nPuoi chiudere la missione.", 600)
    log("rilievo completato: " .. stato.fatti .. " punti")
    return nil
  end
  local budget = PUNTI_PER_PASSO
  while budget > 0 do
    local j = #stato.riga
    if j >= r.ny then
      f:write(stato.i .. "," .. table.concat(stato.riga, ";") .. "\n")
      f:flush()      -- se DCS si chiude a meta', le righe gia' scritte restano utilizzabili
      stato.riga = {}
      stato.i = stato.i + 1
      if stato.i >= r.nx then
        stato.regione = stato.regione + 1
        stato.i = 0
        if REGIONI[stato.regione] then iniziaRegione(REGIONI[stato.regione]) end
        return timer.getTime() + 0.01
      end
    else
      local x = r.x0 + stato.i * r.passo
      local z = r.y0 + j * r.passo
      local ok, v = pcall(misura, x, z)
      stato.riga[j + 1] = ok and v or "E"
      stato.fatti = stato.fatti + 1
      budget = budget - 1
    end
  end
  local perc = math.floor(stato.fatti * 100 / math.max(totale, 1))
  if perc >= stato.ultimaPercentuale + 5 then
    stato.ultimaPercentuale = perc
    messaggio(string.format("Rilievo del terreno: %d%%  (%d / %d punti)\nNon mettere in pausa la simulazione.",
      perc, stato.fatti, totale), 15)
  end
  return timer.getTime() + 0.01
end

if #REGIONI == 0 then
  messaggio("RILIEVO: nessuna regione definita.", 60)
  f:close()
  return
end

iniziaRegione(REGIONI[1])
messaggio(string.format("Rilievo del terreno avviato: %d punti in %d regioni.\nLascia girare la missione fino al messaggio RILIEVO COMPLETATO.",
  totale, #REGIONI), 20)
timer.scheduleFunction(passo, nil, timer.getTime() + 3)
