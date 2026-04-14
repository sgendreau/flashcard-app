import { useWindowDimensions } from 'react-native';

export function useResponsive() {
  const { width, height } = useWindowDimensions();
  const isTablet = width >= 768;
  const isLandscape = width > height;
  const columns = isTablet ? (isLandscape ? 3 : 2) : 1;
  const cardWidth = isTablet ? (width - 60) / columns : width - 40;
  const fontSize = isTablet ? 1.15 : 1;

  return { isTablet, isLandscape, columns, cardWidth, width, height, fontSize };
}
