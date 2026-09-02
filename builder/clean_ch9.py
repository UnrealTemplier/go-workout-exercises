import json

with open('builder/chapter9_data.json', 'r', encoding='utf-8') as f:
    exercises = json.load(f)

for ex in exercises:
    num = ex['num']
    if num == 2:
        ex['code_blocks'][0]['code'] = r"""package main

import "fmt"

func main() {
	var m map[string]int

	fmt.Printf("1. Состояние: isNil = %t, len = %d\n", m == nil, len(m))

	val := m["любой_ключ"]
	fmt.Printf("2. Чтение из nil-мапы: val = %d\n\n", val)

	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("⚠️ 3. Перехвачена паника: %v\n", r)
			}
		}()
		m["key"] = 1
	}()

	m = make(map[string]int)
	m["key"] = 1
	fmt.Printf("\n4. После make: m[\"key\"] = %d\n", m["key"])
}"""
    elif num == 11:
        ex['code_blocks'][0]['code'] = r"""package main

import "fmt"

func main() {
	m := make(map[string][]int)

	m["scores"] = append(m["scores"], 10)
	m["scores"] = append(m["scores"], 20)
	m["scores"] = append(m["scores"], 30)

	fmt.Printf("1. Срез в мапе: %v | len = %d, cap = %d\n",
		m["scores"], len(m["scores"]), cap(m["scores"]))

	temp := m["scores"]
	temp = append(temp, 40)

	fmt.Printf("2. temp: %v (len=%d)\n", temp, len(temp))
	fmt.Printf("3. m[\"scores\"]: %v (len=%d)\n", m["scores"], len(m["scores"]))
}"""
    elif num == 22:
        ex['code_blocks'][0]['code'] = r"""package main

import "fmt"

func main() {
	var m map[string]int

	fmt.Printf("1. Чтение из nil-мапы: m[\"a\"] = %d\n", m["a"])

	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("2. Перехвачена паника: %v\n", r)
			}
		}()
		m["key"] = 1
	}()

	m = make(map[string]int)
	m["key"] = 1
	fmt.Printf("3. Успешная запись: m[\"key\"] = %d\n", m["key"])
}"""
    elif num == 24:
        ex['code_blocks'][0]['code'] = r"""package main

import "fmt"

func main() {
	var m map[string]int

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Поймана ожидаемая паника: %v\n", r)

			fixedMap := make(map[string]int)
			fixedMap["a"] = 1
			fmt.Printf("Исправлено через make: fixedMap[\"a\"] = %d\n", fixedMap["a"])
		}
	}()

	m["a"] = 1
}"""
    elif num == 45:
        ex['code_blocks'][0]['code'] = r"""package main

import (
	"cmp"
	"fmt"
	"slices"
	"strings"
)

type WordFreq struct {
	Word  string
	Count int
}

func TopKWords(text string, k int) []WordFreq {
	counts := make(map[string]int)
	for _, w := range strings.Fields(strings.ToLower(text)) {
		cleanWord := strings.Trim(w, ".,!?;:\"")
		if cleanWord != "" {
			counts[cleanWord]++
		}
	}

	freqs := make([]WordFreq, 0, len(counts))
	for w, c := range counts {
		freqs = append(freqs, WordFreq{Word: w, Count: c})
	}

	slices.SortFunc(freqs, func(a, b WordFreq) int {
		if n := cmp.Compare(b.Count, a.Count); n != 0 {
			return n
		}
		return cmp.Compare(a.Word, b.Word)
	})

	if k > len(freqs) {
		k = len(freqs)
	}
	return freqs[:k]
}

func main() {
	text := "Go is expressive concise clean and efficient Go compiles quickly to machine code Go is fast statically typed compiled language"

	top5 := TopKWords(text, 5)

	fmt.Println("=== ТОП-5 САМЫХ ЧАСТЫХ СЛОВ ===")
	for i, wf := range top5 {
		fmt.Printf("  #%d. %-10s -> %d раз(а)\n", i+1, wf.Word, wf.Count)
	}
}"""
    elif num == 55:
        ex['code_blocks'][0]['code'] = r"""package main

import "fmt"

func main() {
	ipMap := map[[4]byte]string{
		{127, 0, 0, 1}: "localhost",
		{8, 8, 8, 8}:   "google-dns",
	}
	fmt.Printf("1. Массив в ключе: %s\n", ipMap[[4]byte{8, 8, 8, 8}])

	ch1 := make(chan int)
	chMap := map[chan int]string{ch1: "Канал заказов"}
	fmt.Printf("2. Канал в ключе:  %s\n", chMap[ch1])

	anyMap := make(map[any]string)
	anyMap["строка"] = "ОК"
	anyMap[100] = "ОК"

	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️ 3. Паника в рантайме: %v\n", r)
		}
	}()

	anyMap[[]int{1, 2, 3}] = "КРАШ!"
}"""

with open('builder/chapter9_data.json', 'w', encoding='utf-8') as f:
    json.dump(exercises, f, ensure_ascii=False, indent=2)

print('Cleaned chapter9_data.json')
