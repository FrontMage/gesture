function solution(A, B) {
  A.sort();
  B.sort();

  let i = 0;
  let j = 0;
  while (i < A.length && j < B.length) {
    if (A[i] == B[j]) {
      return A[i];
    }
    if (A[i] > B[j]) {
      j++;
    }
    if (A[i] < B[j]) {
      i++;
    }
  }
  return -1;
}

console.log(solution([4, 3, 2, 1], [1, 5, 6, 7]));
