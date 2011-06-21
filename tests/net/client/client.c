#include <string.h>
#include <unistd.h>
#include <netdb.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define BUFSIZE 2

int main(int argc, char *argv[])
{
    hostent *host;
    struct sockaddr_in serverSock;
    struct sockaddr_in other;
    int mySocket;
    int port;
    char buf[BUFSIZE];
    int size;
    socklen_t addrlen;
    
    if (argc != 3)
    {
        fprintf(stderr, "Pouziti:\n\t%s adresa port\n", argv[0]);
        return 1;
    }
    port = atoi(argv[2]);
    
    if ((host = gethostbyname(argv[1])) == NULL)
    {
        fprintf(stderr, "Bad address\n");
        return 1;
    }
    
    if ((mySocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        fprintf(stderr, "Cannot create socket\n");
        return 1;
    }

    serverSock.sin_family = AF_INET;
    serverSock.sin_port = htons(port);
    memcpy(&(serverSock.sin_addr), host->h_addr, host->h_length);
    
    char c = 'a';
    while (1)
    {
        char temp[2];
    	sprintf(temp,"%c", c);
	    
	    if ((size = sendto(mySocket, temp, strlen(temp), 0, (sockaddr*)&serverSock, sizeof(serverSock))) == -1)
        {
            perror("sendto: ");
        }
        else
        {
            fprintf(stdout, "send %c\n", c);
            fflush(stdout);
        }
        
	    addrlen = sizeof(other);
        if ((size = recvfrom(mySocket, buf, BUFSIZE, 0, (sockaddr*)&other, &addrlen)) == -1)
        {       
            perror("recvfrom: ");
        }
        else
        {
            buf[size] = '\0';
            fprintf(stdout, "recv %s\n", buf);
            fflush(stdout);
        }
        if (c == 'z')
            c = 'a';
        else
            c++;
            
        sleep(3);
    }
    close(mySocket);
    return 0;
}
