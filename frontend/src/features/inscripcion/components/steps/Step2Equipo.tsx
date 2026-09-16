"use client";

import { Plus, Search, Shirt, Trash2, Trophy, Users } from "lucide-react";
import { useEffect, useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuthStore } from "@/features/auth/store/auth.store";
import type { DeportistaWizardData, InscripcionPayload } from "../../schemas";
import { getDisciplinas } from "../../services/catalog.service";

const TALLAS = ["XS", "S", "M", "L", "XL", "XXL"] as const;
const ROLES = ["Jugador", "Capitán", "Delegado"] as const;

export function Step2Equipo({
  form,
}: {
  form: UseFormReturn<InscripcionPayload>;
}) {
  const user = useAuthStore((s) => s.user);
  const {
    watch,
    setValue,
    formState: { errors },
  } = form;
  const deportistas = watch("deportistas") || [];
  const teamName = watch("teamName");

  const [disciplinas, setDisciplinas] = useState<any[]>([]);
  const [activeDisc, setActiveDisc] = useState<string | null>(null);
  const [newPlayer, setNewPlayer] = useState<Partial<DeportistaWizardData>>({
    tipoDocumento: "DNI",
    rolDisciplina: "Jugador",
    acreditacion: "Verificación en padrón",
    shirtSize: "M",
  });

  useEffect(() => {
    getDisciplinas().then((res) => {
      if (res.success && res.data) {
        setDisciplinas(res.data);
        if (res.data.length > 0) setActiveDisc(res.data[0].id);
      }
    });
  }, []);

  const fillResponsableData = () => {
    if (user) {
      setNewPlayer((prev) => ({
        ...prev,
        tipoDocumento: user.tipoDocumento as "DNI" | "CE" | "PAS",
        numeroDocumento: user.numeroDocumento,
        nombres: user.nombres,
        apellidos: user.apellidos,
        rolDisciplina: "Delegado",
      }));
    }
  };

  const handleDocChange = (val: string) => {
    setNewPlayer((prev) => ({ ...prev, numeroDocumento: val }));
    const existing = deportistas.find((d) => d.numeroDocumento === val);
    if (existing) {
      setNewPlayer((prev) => ({
        ...prev,
        nombres: existing.nombres,
        apellidos: existing.apellidos,
        tipoDocumento: existing.tipoDocumento,
        shirtSize: existing.shirtSize,
      }));
    }
  };

  const handleAddPlayer = () => {
    if (
      !activeDisc ||
      !newPlayer.numeroDocumento ||
      !newPlayer.nombres ||
      !newPlayer.apellidos
    )
      return;

    const existingIdx = deportistas.findIndex(
      (d) => d.numeroDocumento === newPlayer.numeroDocumento,
    );

    if (existingIdx >= 0) {
      const updated = [...deportistas];
      const player = updated[existingIdx];
      if (!player.disciplinaIds.includes(activeDisc)) {
        player.disciplinaIds.push(activeDisc);
        setValue("deportistas", updated);
      }
    } else {
      const playerToAdd: DeportistaWizardData = {
        tipoDocumento: newPlayer.tipoDocumento as "DNI" | "CE" | "PAS",
        numeroDocumento: newPlayer.numeroDocumento!,
        nombres: newPlayer.nombres!,
        apellidos: newPlayer.apellidos!,
        genero: newPlayer.genero as "V" | "M" | null | undefined,
        telefono: newPlayer.telefono || null,
        rolDisciplina: newPlayer.rolDisciplina as
          | "Capitán"
          | "Delegado"
          | "Jugador",
        acreditacion: "Verificación en padrón",
        disciplinaIds: [activeDisc],
        shirtSize: newPlayer.shirtSize as
          | (typeof TALLAS)[number]
          | null
          | undefined,
      };
      setValue("deportistas", [...deportistas, playerToAdd]);
    }

    setNewPlayer({
      tipoDocumento: "DNI",
      rolDisciplina: "Jugador",
      acreditacion: "Verificación en padrón",
      shirtSize: "M",
    });
  };

  const handleRemovePlayer = (docNum: string, discId: string) => {
    const updated = deportistas
      .map((d) => {
        if (d.numeroDocumento === docNum) {
          return {
            ...d,
            disciplinaIds: d.disciplinaIds.filter((id) => id !== discId),
          };
        }
        return d;
      })
      .filter((d) => d.disciplinaIds.length > 0);
    setValue("deportistas", updated);
  };

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Nombre del equipo */}
      <div className="space-y-2">
        <Label htmlFor="teamName" className="flex items-center gap-2">
          <Trophy className="size-4 text-[#312e8e]" /> Nombre del equipo
        </Label>
        <Input
          id="teamName"
          placeholder="Ej. Los Invictos 2002"
          className="input-brand bg-white"
          value={teamName || ""}
          onChange={(e) => setValue("teamName", e.target.value)}
        />
        {errors.teamName && (
          <p className="text-sm text-destructive">{errors.teamName.message}</p>
        )}
      </div>

      {/* Tabs de disciplinas */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {disciplinas.map((disc) => (
          <Button
            key={disc.id}
            type="button"
            variant={activeDisc === disc.id ? "default" : "outline"}
            onClick={() => setActiveDisc(disc.id)}
            className="whitespace-nowrap"
          >
            {disc.nombre}
          </Button>
        ))}
      </div>

      {activeDisc && (
        <Card className="border border-[#312e8e]/20 shadow-lg">
          <CardHeader className="border-b bg-slate-50 pb-4">
            <CardTitle className="text-lg text-[#312e8e]">
              {disciplinas.find((d) => d.id === activeDisc)?.nombre}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            {/* Nómina actual */}
            <div className="space-y-3">
              <Label className="text-xs font-bold uppercase text-muted-foreground">
                Nómina actual
              </Label>
              {deportistas.filter((d) => d.disciplinaIds.includes(activeDisc))
                .length === 0 ? (
                <p className="text-sm italic text-slate-500">
                  No hay deportistas en esta disciplina.
                </p>
              ) : (
                <div className="space-y-2">
                  {deportistas
                    .filter((d) => d.disciplinaIds.includes(activeDisc))
                    .map((d) => (
                      <div
                        key={`${d.numeroDocumento}-${activeDisc}`}
                        className="flex items-center justify-between border bg-white p-3 rounded-lg shadow-sm"
                      >
                        <div>
                          <p className="text-sm font-bold">
                            {d.apellidos}, {d.nombres}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {d.tipoDocumento}: {d.numeroDocumento} | Rol:{" "}
                            {d.rolDisciplina} | Talla: {d.shirtSize ?? "—"}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-500 hover:bg-red-50"
                          onClick={() =>
                            handleRemovePlayer(d.numeroDocumento, activeDisc)
                          }
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      </div>
                    ))}
                </div>
              )}
            </div>

            {/* Mini form */}
            <div className="space-y-4 rounded-xl border border-[#312e8e]/10 bg-[#f4f6fb] p-4">
              <div className="flex items-center justify-between">
                <h4 className="flex items-center gap-2 text-sm font-bold text-[#312e8e]">
                  <Plus className="size-4" /> Añadir deportista
                </h4>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={fillResponsableData}
                  className="text-xs"
                >
                  Usar mis datos
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Tipo Doc</Label>
                  <Select
                    value={newPlayer.tipoDocumento ?? "DNI"}
                    onValueChange={(v) =>
                      setNewPlayer({
                        ...newPlayer,
                        tipoDocumento: v as "DNI" | "CE" | "PAS",
                      })
                    }
                  >
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DNI">DNI</SelectItem>
                      <SelectItem value="CE">CE</SelectItem>
                      <SelectItem value="PAS">PAS</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Número Doc</Label>
                  <div className="relative">
                    <Input
                      className="bg-white pr-8"
                      value={newPlayer.numeroDocumento || ""}
                      onChange={(e) => handleDocChange(e.target.value)}
                      placeholder="12345678"
                    />
                    <Search className="absolute right-2 top-2.5 size-4 text-muted-foreground" />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Nombres</Label>
                  <Input
                    className="bg-white"
                    value={newPlayer.nombres || ""}
                    onChange={(e) =>
                      setNewPlayer({ ...newPlayer, nombres: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Apellidos</Label>
                  <Input
                    className="bg-white"
                    value={newPlayer.apellidos || ""}
                    onChange={(e) =>
                      setNewPlayer({ ...newPlayer, apellidos: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-1 text-xs">
                    <Shirt className="size-3.5" /> Talla camiseta
                  </Label>
                  <Select
                    value={newPlayer.shirtSize ?? "M"}
                    onValueChange={(v) =>
                      setNewPlayer({
                        ...newPlayer,
                        shirtSize: v as (typeof TALLAS)[number],
                      })
                    }
                  >
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TALLAS.map((t) => (
                        <SelectItem key={t} value={t}>
                          {t}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Rol en disciplina</Label>
                  <Select
                    value={newPlayer.rolDisciplina ?? "Jugador"}
                    onValueChange={(v) =>
                      setNewPlayer({
                        ...newPlayer,
                        rolDisciplina: v as (typeof ROLES)[number],
                      })
                    }
                  >
                    <SelectTrigger className="bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLES.map((r) => (
                        <SelectItem key={r} value={r}>
                          {r}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                type="button"
                onClick={handleAddPlayer}
                className="btn-brand-gradient w-full"
              >
                <Users className="mr-2 size-4" /> Guardar en la nómina
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {errors.deportistas && (
        <p className="text-sm font-medium text-red-500">
          {errors.deportistas.message}
        </p>
      )}
    </div>
  );
}
