
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

plt.rc('font', family="Pretendard")

def load_sql(host, user, password, database):
    try:
        engine_url = f'mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8'
        engine = create_engine(engine_url)
        query = """SELECT *
        FROM customer_record
        WHERE revisit > 1
        ORDER BY customer_id;
        """
        # Run query with parameters
        df = pd.read_sql_query(query, engine)
        customer_store_visits = df.groupby(['customer_id', 'store_name']).size().unstack(fill_value=0)
        customer_store_visits
        return customer_store_visits
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def make_clusters(customer_store_visits):
    # PCA를 사용하여 차원 축소
    pca = PCA(random_state=100)
    pca.fit(customer_store_visits)
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    n_components = np.where(cumulative_variance >= 0.7)[0][0] + 1

    # 설명된 분산을 바탕으로 다시 PCA 실행
    pca = PCA(n_components=n_components, random_state=100)
    reduced_data = pca.fit_transform(customer_store_visits)

    # KMeans를 이용해 다양한 k 값에 대해 군집화 실행
    sse = {}
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, random_state=100, n_init=10)
        kmeans.fit(reduced_data)
        sse[k] = kmeans.inertia_

    # SSE의 변화율을 계산
    sse_diff = {}
    for k in range(2, 11):
        sse_diff[k] = abs(sse[k] - sse[k-1])

    # 변화율의 변화를 계산
    sse_diff_diff = {}
    for k in range(3, 11):
        sse_diff_diff[k] = abs(sse_diff[k] - sse_diff[k-1])

    # 변화율의 감소가 가장 큰 첫 번째 지점 찾기
    k_optimal = min(sse_diff_diff, key=sse_diff_diff.get)
    print(f"Optimal number of clusters: {k_optimal}")

    # 최적의 군집 개수로 다시 KMeans 실행
    kmeans = KMeans(n_clusters=k_optimal, random_state=100, n_init=10)
    clusters = kmeans.fit_predict(reduced_data)

    # 군집 결과를 데이터에 추가
    customer_store_visits['Cluster'] = clusters
    cluster_store_visits = customer_store_visits.groupby('Cluster')[customer_store_visits.columns[:-1]].sum()

    # 각 군집별 상위 매장 집계
    top_stores_by_cluster = {}
    for cluster in cluster_store_visits.index:
        top_stores = cluster_store_visits.loc[cluster].nlargest(5).reset_index()
        top_stores.columns = ['store_name', 'visits']
        top_stores['Cluster'] = cluster
        top_stores_by_cluster[cluster] = top_stores

    # 결과 시각화
    top_stores_combined = pd.concat(top_stores_by_cluster.values())
    plt.figure(figsize=(12, 8))
    bubble_chart = sns.scatterplot(data=top_stores_combined, x='Cluster', y='store_name', size='visits', hue='Cluster', sizes=(100, 2000), legend=None)
    plt.title('Top 5 Stores Visited by Cluster (Bubble Chart)')
    plt.xlabel('Cluster')
    plt.ylabel('Store Name')
    plt.grid(True)
    plt.savefig('mnt/data/my_graph2.png', bbox_inches='tight')
    cluster_store_visits.reset_index(inplace=True)
    return cluster_store_visits


def extract_top_stores_by_cluster(clustered_data):
    top_stores_by_cluster = {}
    for cluster in clustered_data['Cluster'].unique():
        # 현재 군집의 데이터만 필터링
        cluster_data = clustered_data[clustered_data['Cluster'] == cluster]
        # 모든 매장에 대해 방문 수를 합산
        store_sums = cluster_data.drop(columns='Cluster').sum().sort_values(ascending=False).head(5)
        
        # 상위 5개 매장 정보를 DataFrame으로 변환
        top_stores = pd.DataFrame({
            'store_name': store_sums.index,
            'visits': store_sums.values,
            'Cluster': cluster
        })
        top_stores_by_cluster[cluster] = top_stores

    # 모든 군집의 상위 매장 정보를 하나의 DataFrame으로 합치기
    all_top_stores = pd.concat(top_stores_by_cluster.values())
    all_top_stores.reset_index(inplace=True,drop=True)
    
    return all_top_stores

def show_5_stores(store_name, data):
    data = data.sort_values(by=['Cluster', 'visits'], ascending = [True, False])

    cluster_number = max(data[data['store_name'] == store_name]['Cluster'])
    cluster_list = list(data[data['Cluster'] == cluster_number]['store_name'])
    cluster_list.remove(store_name)
    return cluster_list

def testfunc(customer_store_visits):
    # PCA를 사용하여 차원 축소
    pca = PCA(random_state=100)
    pca.fit(customer_store_visits)
    cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
    n_components = np.where(cumulative_variance >= 0.7)[0][0] + 1

    # 설명된 분산을 바탕으로 다시 PCA 실행
    pca = PCA(n_components=n_components, random_state=100)
    reduced_data = pca.fit_transform(customer_store_visits)

    # KMeans를 이용해 다양한 k 값에 대해 군집화 실행
    sse = {}
    for k in range(1, 11):
        kmeans = KMeans(n_clusters=k, random_state=100, n_init=10)
        kmeans.fit(reduced_data)
        sse[k] = kmeans.inertia_

    # SSE의 변화율을 계산
    sse_diff = {}
    for k in range(2, 11):
        sse_diff[k] = abs(sse[k] - sse[k-1])

    # 변화율의 변화를 계산
    sse_diff_diff = {}
    for k in range(3, 11):
        sse_diff_diff[k] = abs(sse_diff[k] - sse_diff[k-1])

    # 변화율의 감소가 가장 큰 첫 번째 지점 찾기
    k_optimal = min(sse_diff_diff, key=sse_diff_diff.get)
    print(f"Optimal number of clusters: {k_optimal}")

    # 최적의 군집 개수로 다시 KMeans 실행
    kmeans = KMeans(n_clusters=k_optimal, random_state=100, n_init=10)
    clusters = kmeans.fit_predict(reduced_data)

    # 군집 결과를 데이터에 추가
    customer_store_visits['Cluster'] = clusters
    cluster_store_visits = customer_store_visits.groupby('Cluster')[customer_store_visits.columns[:-1]].sum()

    top_stores_by_cluster = {}
    for cluster in cluster_store_visits.index[:2]:
        top_stores = cluster_store_visits.loc[cluster].nlargest(5).reset_index()
        top_stores.columns = ['store_name', 'visits']
        top_stores['Cluster'] = cluster
        top_stores_by_cluster[cluster] = top_stores

    top_stores_combined = pd.concat(top_stores_by_cluster.values())
    # Plotting the bubble chart with x-axis as integers
    plt.figure(figsize=(4,8))
    bubble_chart = sns.scatterplot(data=top_stores_combined, x='Cluster', y='store_name', size='visits', hue='Cluster', sizes=(100, 2000), legend=None)
    bubble_chart.tick_params(axis='both', which='major', labelsize=20)
    plt.title('클러스터별 가장 재방문 많이한 가게 Top 5',fontsize=25)
    plt.xlabel('Cluster',fontsize=20)
    plt.xticks(ticks=range(len(top_stores_combined['Cluster'].unique())), labels=top_stores_combined['Cluster'].unique().astype(int), fontsize=15)
    plt.grid(True)

    # Adjust x-axis limits to ensure circles are not cut off
    plt.tight_layout(pad=100.0)
    plt.xlim(top_stores_combined['Cluster'].min() - 0.5, top_stores_combined['Cluster'].max() + 0.5)

    plt.savefig('mnt/data/my_graph3.png', bbox_inches='tight')

