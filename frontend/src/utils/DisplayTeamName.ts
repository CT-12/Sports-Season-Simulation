/**
 * 將後端返回的球隊名稱轉換為前端顯示用的名稱
 * @param teamName 後端的球隊名稱
 * @returns 用於前端顯示的球隊名稱
 */
export function getDisplayTeamName(teamName: string): string {
  if (teamName === 'Athletics') {
    return 'Oakland Athletics';
  }
  return teamName;
}

/**
 * 將前端顯示的球隊名稱轉換回後端使用的名稱
 * @param displayName 前端顯示的球隊名稱
 * @returns 後端使用的球隊名稱
 */
export function getBackendTeamName(displayName: string): string {
  if (displayName === 'Oakland Athletics') {
    return 'Athletics';
  }
  return displayName;
}
