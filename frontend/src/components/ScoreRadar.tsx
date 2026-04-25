import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface RadarDimension {
  subject: string;
  score: number;
  fullMark: number;
}

interface ScoreRadarProps {
  dimensions: RadarDimension[];
  color?: string;
}

export default function ScoreRadar({ dimensions, color = '#7c3aed' }: ScoreRadarProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={dimensions} margin={{ top: 16, right: 32, bottom: 16, left: 32 }}>
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fontSize: 12, fill: '#6b7280' }}
        />
        <Radar
          name="Score"
          dataKey="score"
          stroke={color}
          fill={color}
          fillOpacity={0.25}
          strokeWidth={2}
        />
        <Tooltip
          formatter={(value) => [`${Number(value).toFixed(0)}/100`, 'Score']}
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

export function matchRadarDimensions(match: {
  research_direction_score: number;
  mentorship_style_score: number;
  funding_stability_score: number;
  culture_fit_score: number;
  technical_skills_score: number;
}): RadarDimension[] {
  return [
    { subject: 'Research', score: match.research_direction_score, fullMark: 100 },
    { subject: 'Mentorship', score: match.mentorship_style_score, fullMark: 100 },
    { subject: 'Funding', score: match.funding_stability_score, fullMark: 100 },
    { subject: 'Culture', score: match.culture_fit_score, fullMark: 100 },
    { subject: 'Skills', score: match.technical_skills_score, fullMark: 100 },
  ];
}

export function chemistryRadarDimensions(scores: {
  research_alignment: number;
  mentorship_compatibility: number;
  culture_fit: number;
  communication_fit: number;
  red_flags: number;
}): RadarDimension[] {
  return [
    { subject: 'Research', score: scores.research_alignment, fullMark: 100 },
    { subject: 'Mentorship', score: scores.mentorship_compatibility, fullMark: 100 },
    { subject: 'Culture', score: scores.culture_fit, fullMark: 100 },
    { subject: 'Communication', score: scores.communication_fit, fullMark: 100 },
    { subject: 'No Red Flags', score: scores.red_flags, fullMark: 100 },
  ];
}
