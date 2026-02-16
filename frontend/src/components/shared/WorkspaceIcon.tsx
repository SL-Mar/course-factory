import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { SizeProp } from "@fortawesome/fontawesome-svg-core";
import {
  faFolder,
  faAnchor,
  faWind,
  faChartLine,
  faCommentDots,
  faSailboat,
  faCode,
  faScrewdriverWrench,
  faNewspaper,
  faBookOpen,
  faArrowTrendUp,
  faFile,
  faGlobe,
  faFlask,
  faBriefcase,
  faLightbulb,
  faBullseye,
  faRocket,
  faShield,
  faDatabase,
} from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";

const ICON_MAP: Record<string, IconDefinition> = {
  folder: faFolder,
  anchor: faAnchor,
  wind: faWind,
  "chart-line": faChartLine,
  "comment-dots": faCommentDots,
  sailboat: faSailboat,
  code: faCode,
  "screwdriver-wrench": faScrewdriverWrench,
  newspaper: faNewspaper,
  "book-open": faBookOpen,
  "arrow-trend-up": faArrowTrendUp,
  file: faFile,
  globe: faGlobe,
  flask: faFlask,
  briefcase: faBriefcase,
  lightbulb: faLightbulb,
  bullseye: faBullseye,
  rocket: faRocket,
  shield: faShield,
  database: faDatabase,
};

/** All available icon keys for the picker */
export const ICON_KEYS = Object.keys(ICON_MAP);

interface WorkspaceIconProps {
  icon: string;
  size?: SizeProp;
  className?: string;
}

export function WorkspaceIcon({ icon, size = "sm", className }: WorkspaceIconProps) {
  const def = ICON_MAP[icon];
  if (def) {
    return <FontAwesomeIcon icon={def} size={size} className={className} />;
  }
  // Fallback: if icon is an emoji string or unknown key, render as text
  if (icon) {
    return <span className={className}>{icon}</span>;
  }
  return <FontAwesomeIcon icon={faFolder} size={size} className={className} />;
}
