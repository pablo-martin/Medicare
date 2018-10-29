import numpy as np

def create_deck(N = 26, M = 2, shuffle = 1):
    cards_per_suit = int(np.float(N)/M)
    suits = 'abcdefgh'
    deck = []
    for suit in range(M):
        deck += suits[suit] * cards_per_suit
    np.random.seed(shuffle)
    np.random.shuffle(deck)
    return deck

def draw_cards(deck):
    P = 0
    N = len(deck)
    card = deck[0]
    for draw in range(1,N):
        new_card = deck[draw]
        if new_card == card:
            P += 1
        card = new_card
    return P

def run_simulations(N = 26, M = 2, noSimulations = 10000000):
    P = np.full(noSimulations, np.NaN)
    for SHUFFLE in range(noSimulations):
        deck = create_deck(N = N, M = M, shuffle = SHUFFLE)
        P[SHUFFLE] = draw_cards(deck)
    return P


if __name__ == '__main__':
    noSimulations = 10000000
    P26 = run_simulations(N = 26, M = 2, noSimulations = noSimulations)
    P52 = run_simulations(N = 52, M = 4, noSimulations = noSimulations)
    print('mean = %1.10f' %np.nanmean(P26)) #12.0002153000
    print('stdev = %1.10f' %np.nanstd(P26)) #2.4981817095
    print('mean = %1.10f' %np.nanmean(P52)) #11.9997437000
    print('stdev = %1.10f' %np.nanstd(P52)) #3.0291540790
    '''
    conditional probability P(a|b) = P(A intersection B) / P(B)
    '''
    numerator = np.float(np.sum(P26 > 12)) / len(P26)
    denominator = np.float(np.sum(P26 > 6)) / len(P26)
    print('conditional probability is %1.10f' %(numerator/denominator)) #0.4236454385

    numerator = np.float(np.sum(P52 > 12)) / len(P52)
    denominator = np.float(np.sum(P52 > 6)) / len(P52)
    print('conditional probability is %1.10f' %(numerator/denominator)) #0.4360506938
