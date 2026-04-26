import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';

interface RadarDimension {
  subject: string;
  score: number;
  fullMark: number;
}

interface ScoreRadarProps {
  dimensions: RadarDimension[];
  height?: number;
}

export default function ScoreRadar({ dimensions, height = 320 }: ScoreRadarProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart
        data={dimensions}
        margin={{ top: 24, right: 48, bottom: 24, left: 48 }}
        outerRadius="78%"
      >
        <PolarGrid stroke="var(--color-line)" strokeWidth={1} />
        <PolarAngleAxis
          dataKey="subject"
          tick={{
            fontSize: 11,
            fill: 'var(--color-soft)',
            fontFamily: 'Inter, sans-serif',
            letterSpacing: '0.04em',
          }}
        />
        <Radar
          name="Score"
          dataKey="score"
          stroke="var(--color-forest)"
          fill="var(--color-forest)"
          fillOpacity={0.2}
          strokeWidth={1.5}
          strokeLinejoin="round"
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
    { subject: 'No red flags', score: scores.red_flags, fullMark: 100 },
  ];
}
