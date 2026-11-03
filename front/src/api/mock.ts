import type { ConsultationRequest, ConsultationResponse, FollowUpRequest, FollowUpResponse } from '../types';

const sources = [
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
    point: { lat: -34.6042, lng: -58. omitting },
    summary: 'Esta respuesta es una maqueta funcional. Antes de tomar decisiones, verificá los requisitos vigentes en las fuentes oficiales vinculadas.',
    steps: [
      { id:'step-1', title:'Confirmá la clasificación de la actividad', description:'Verificá cómo se encuadra la actividad declarada y qué régimen de habilitación corresponde.', documents:['Descripción precisa de la actividad'], sourceIds:['src-procedures'] },
      { id:'step-2', title:'Validá las condiciones del domicilio', description:'Consultá las condiciones territoriales aplicables al inmueble. La capa del mapa de esta demo es ilustrativa.', documents:['Dirección completa'], sourceIds:['src-territory'] },
      { id:'step-3', title:'Reuní la documentación exigida', description:'Contrastá el listado definitivo de documentación con el trámite oficial vigente.', documents:['Documentación personal y del inmueble, según trámite'], sourceIds:['src-procedures'] },
    ],
    territorialFeatures: [],
    sources,
    limitations: ['Datos y fuentes de demostración: no constituyen una respuesta oficial.', 'El backend debe validar dirección, actividad, fecha de actualización y reglas de correlación.'],
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
