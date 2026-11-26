import type {
  ConsultationRequest, ConsultationResponse, FollowUpRequest, FollowUpResponse,
  RubroReferencias, SourceReference, UseTableResponse,
} from '../types';

const sources: SourceReference[] = [
  { id: 'src-procedures', title: 'Guía oficial de habilitaciones (fuente piloto)', publisher: 'Organismo oficial — reemplazar por fuente validada', url: 'https://buenosaires.gob.ar/', note: 'Referencia de demostración; no usar como asesoramiento oficial.' },
  { id: 'src-territory', title: 'Datos territoriales (capa piloto)', publisher: 'Fuente territorial — reemplazar por dataset seleccionado', url: 'https://data.buenosaires.gob.ar/', note: 'Capa ilustrativa, no representa una validación de zonificación.' },
  { id: 'src-context', title: 'Contexto del área (dataset piloto)', publisher: 'Fuente contextual — reemplazar por dataset seleccionado', url: 'https://data.buenosaires.gob.ar/', note: 'Datos de muestra para probar la experiencia.' },
];

export async function mockConsultation(payload: ConsultationRequest): Promise<ConsultationResponse> {
  await new Promise(resolve => setTimeout(resolve, 450));
  return {
    consultationId: `demo-${Date.now()}`,
    interpretedActivity: payload.activity.trim() || 'actividad comercial',
    normalizedAddress: payload.address.trim() || 'Av. Corrientes 2500, CABA',
    point: payload.point === undefined ? { lat: -34.6042, lng: -58.3816 } : payload.point,
    summary: 'Esta respuesta es una maqueta funcional. Antes de tomar decisiones, verificá los requisitos vigentes en las fuentes oficiales vinculadas.',
    steps: [
      { id:'step-1', title:'Confirmá la clasificación de la actividad', description:'Verificá cómo se encuadra la actividad declarada y qué régimen de habilitación corresponde.', documents:['Descripción precisa de la actividad'], sourceIds:['src-procedures'] },
      { id:'step-2', title:'Validá las condiciones del domicilio', description:'Consultá las condiciones territoriales aplicables al inmueble. La capa del mapa de esta demo es ilustrativa.', documents:['Dirección completa'], sourceIds:['src-territory'] },
      { id:'step-3', title:'Reuní la documentación exigida', description:'Contrastá el listado definitivo de documentación con el trámite oficial vigente.', documents:['Documentación personal y del inmueble, según trámite'], sourceIds:['src-procedures'] },
    ],
    territorialFeatures: [],
    sources,
    limitations: ['Datos de demostración: no constituyen una respuesta oficial.', 'El backend debe validar dirección, actividad, fecha de actualización y reglas de correlación.'],
  };
}

export async function mockFollowUp(payload: FollowUpRequest): Promise<FollowUpResponse> {
  await new Promise(resolve => setTimeout(resolve, 300));
  return {
    answer: `La consulta "${payload.question}" necesita verificarse contra los datos oficiales integrados. En esta versión de demostración no se genera una conclusión nueva.`,
    sourceIds: ['src-procedures'],
    limitations: ['Respuesta simulada; el modelo de IA aún no está conectado.'],
  };
}

/** The official source is cited even in mock mode, but no rubro is invented. */
const useTableSource: SourceReference = {
  id: 'usig-ciudad-3d',
  title: 'Ciudad 3D — Cuadro de usos',
  publisher: 'USIG, Gobierno de la Ciudad de Buenos Aires',
  url: 'https://ciudad3d.buenosaires.gob.ar',
};

export async function mockUseTable(): Promise<UseTableResponse> {
  return {
    smp: null,
    official_address: null,
    mix_area: null,
    categories: [],
    source: useTableSource,
    limitations: ['Modo demostración: el Cuadro de Usos oficial no está disponible. No se mostraron rubros simulados.'],
  };
}

export async function mockRubroReferencias(): Promise<RubroReferencias> {
  return {
    permitido_mixtura_de_usos: [],
    bicicletas: [],
    estacionamientos: [],
    cargaydescarga: [],
    observaciones: null,
    source: useTableSource,
    limitations: ['Modo demostración: las condiciones oficiales del rubro no están disponibles.'],
  };
}
